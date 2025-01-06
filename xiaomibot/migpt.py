import asyncio
import json
import logging
import re
import time
from miservice import MiAccount,MiIOService,MiNAService,miio_command
from aiohttp import ClientSession,ClientTimeout
from pathlib import Path
from rich.logging import RichHandler
from xiaomibot.config import (
    COOKIE_TEMPLATE,
    LATEST_ASK_API,
    WAKEUP_KEYWORD,
    Config
)
from xiaomibot.hass import HASS
from xiaomibot.utils import parse_cookie_string


class MIGPT:

    def __init__(self, config: Config):
        self.config = config
        self.mi_token_home = Path.home() / ".mi.token"
        self.last_timestamp = int(time.time() * 1000) 
        self.cookie_jar = None
        self.device_id = ""
        self.mina_service = None
        self.miio_service = None
        self.polling_event = asyncio.Event()
        self.last_record = asyncio.Queue(1)
        self.hass = HASS()

        # setup logger
        self.log = logging.getLogger("xiaogpt")
        self.log.setLevel(logging.DEBUG if config.verbose else logging.INFO)
        self.log.addHandler(RichHandler())
        self.log.debug(config)
        self.mi_session = ClientSession()

    def get_cookie(self):
        with open(self.mi_token_home) as f:
            user_data = json.loads(f.read())
        user_id = user_data.get("userId")
        service_token = user_data.get("micoapi")[1]
        cookie_string = COOKIE_TEMPLATE.format(device_id=self.device_id, service_token=service_token, user_id=user_id)
        return parse_cookie_string(cookie_string)

    async def init_all_data(self):
        #登录账号
        account = MiAccount(
            self.mi_session,
            self.config.account, 
            self.config.password,
            str(self.mi_token_home)
            )
        self.log.info(self.config.account)
        print(self.config.password)
        if self.config.account == None or self.config.password==None :
           raise Exception((f"未获取到账号密码")  )
        
        print(f"登录：{self.config.account} {self.config.password}")
        await account.login("micoapi")
        self.mina_service = MiNAService(account)
        self.miio_service = MiIOService(account)
        #获取设备id
        devices = await self.miio_service.device_list()
        self.config.mi_did = next(
                    d["did"]
                    for d in devices
                    if d["model"].endswith(self.config.hardware.lower())
        )
        print(f"mi_did: {self.config.mi_did}")
        hardware_data = await self.mina_service.device_list()
        for h in hardware_data:
            if did := self.config.mi_did:
                if h.get("miotDID", "") == str(did):
                    self.device_id = h.get("deviceID")
                    break
                else:
                    continue
            if h.get("hardware", "") == self.config.hardware:
                self.device_id = h.get("deviceID")
                break
        else:
            raise Exception(f"未找到设备 {self.config.hardware}")
        print(f"device_id: {self.device_id}")
        #获取cookie
        self.mi_session.cookie_jar.update_cookies(self.get_cookie()) 
        self.cookie_jar = self.mi_session.cookie_jar

    async def pull_latest_ask(self):
        async with ClientSession() as session:
            session._cookie_jar = self.cookie_jar
            log_polling = int(self.config.verbose) > 1
            while True:
                if log_polling:
                    self.log.debug("Listening new message, timestamp: %s", self.last_timestamp)
                new_record = await self.get_latest_ask_from_xiaoai(session)
                start = time.perf_counter() #返回性能计数器的值（以小数秒为单位）作为浮点数，即具有最高可用分辨率的时钟，以测量短持续时间。
                if log_polling:
                    self.log.debug("Polling_event, timestamp: %s %s",self.last_timestamp,new_record,)
                await self.polling_event.wait()
                # if self.config.mute_xiaoai and new_record and self.need_ask_gpt(new_record):
                #     await self.stop_if_xiaoai_is_playing()
                if (d := time.perf_counter() - start) < 1: #如果d小于1秒，则等待1-d秒
                    if log_polling:
                        self.log.debug("Sleep %f, timestamp: %s", d, self.last_timestamp)
                    await asyncio.sleep(1 - d)

    async def get_latest_ask_from_xiaoai(self,session:ClientSession):
        for i in range(3): #重试次数 0 1 2
            try:
                r = await session.get(
                    LATEST_ASK_API.format(
                        hardware=self.config.hardware,
                        timestamp=str(int(time.time() * 1000)),
                    ),
                    timeout=ClientTimeout(total=15)
                )
            except Exception as e:
                self.log.error("Failed to get latest ask from xiaoai: %s", e)
                continue
            try:
                data = await r.json()
            except Exception:
                print("数据错误，尝试初始化数据")
                if i == 1: 
                    self.log.debug("Got latest ask from xiaoai: %s", data)
                    await self.init_all_data()
            else:
                if d:= data.get("data"):
                    records = json.loads(d).get("records")
                    if not records:
                        return None
                    last_record = records[0]
                    timestamp = last_record.get("time")
                    if timestamp > self.last_timestamp:
                        try:
                            self.last_record.put_nowait(last_record)
                            self.last_timestamp = timestamp
                            return last_record
                        except asyncio.QueueFull:
                            pass
                    else:
                        return None
        return None
                
    async def run_forever(self):
        await self.init_all_data()
        task = asyncio.create_task(self.pull_latest_ask())
        assert task is not None
        while True:
            self.polling_event.set()
            new_record = await self.last_record.get()
            self.polling_event.clear()
            query = new_record.get("query","").strip()
            #ou-=匹配提示词
            query = re.sub(rf"^({'|'.join(self.config.keyword)})", "", query)
            print(query)
            print("-" * 20)
            print("问题：" + query)
            #处理hass会话
            if query.lower().startswith(self.config.keyword_hass):
                await self.do_tts("..") #静音小爱
                query = query.replace("设置","")
                answer = self.hass.ask(query)
                print(f"hass_ask: {query}  answer: {answer}")
                await self.do_tts(answer)
            #处理播放器会话

            try:
                answer = new_record.get("answers", [])[0]
                if answer.get("type") == "TTS":
                    print("小爱回答：[tts]" + answer.get("tts", {}).get("text"))
                elif answer.get("type") == "LLM":
                    print("小爱回答：[llm]" + answer.get("llm", {}).get("text"))
            except IndexError:
                print("小爱没回")
                
            else:
                print("回答完毕")
            

    async def wakeup_xiaoai(self):
        return await miio_command(
            self.miio_service,
            self.config.mi_did,
            f"{self.config.wakeup_command} {WAKEUP_KEYWORD} 0",
        )
    
    async def get_if_xiaoai_is_playing(self):
        playing_info = await self.mina_service.player_get_status(self.device_id)
        return (json.loads(playing_info.get("data",{}).get("info","{}")).get("state", -1) == 1)

    async def stop_if_xiaoai_is_playing(self):
        is_playing = await self.get_if_xiaoai_is_playing()
        if is_playing:
            self.log.debug("Muting xiaoai")
            await self.mina_service.player_pause(self.device_id)

    async def do_tts(self,value):
        try:
            await self.mina_service.text_to_speech(self.device_id, value)
        except Exception:
            pass
    async def close(self):
        await self.mi_session.close()

