from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any, Iterable
from dotenv import load_dotenv
from pathlib import Path
LATEST_ASK_API = "https://userprofile.mina.mi.com/device_profile/v2/conversation?source=dialogu&hardware={hardware}&timestamp={timestamp}&limit=2"
COOKIE_TEMPLATE = "deviceId={device_id}; serviceToken={service_token}; userId={user_id}"
WAKEUP_KEYWORD = "小爱同学"
HARDWARE_COMMAND_DICT = {
    # hardware: (tts_command, wakeup_command)
    "L15A": ("7-3", "7-4")
}

DEFAULT_COMMAND = ("7-3", "7-4")

KEY_WORD = ("请")
KEY_WORD_HASS = ("打开","关闭","设置")

# simulate_xiaoai_question
MI_ASK_SIMULATE_DATA = {
    "code": 0,
    "message": "Success",
    "data": '{"bitSet":[0,1,1],"records":[{"bitSet":[0,1,1,1,1],"answers":[{"bitSet":[0,1,1,1],"type":"TTS","tts":{"bitSet":[0,1],"text":"Fake Answer"}}],"time":1677851434593,"query":"Fake Question","requestId":"fada34f8fa0c3f408ee6761ec7391d85"}],"nextEndTime":1677849207387}',
}


@dataclass
class Config:
    hardware: str = "L15A"
    account: str = os.getenv("MI_ACCOUNT")
    password: str = os.getenv("MI_PASS")
    mi_did: str = os.getenv("MI_DID")
    keyword: Iterable[str] = KEY_WORD
    keyword_hass: Iterable[str] = KEY_WORD_HASS
    verbose: int = 0

    @property
    def tts_command(self) -> str:
        return HARDWARE_COMMAND_DICT.get(self.hardware, DEFAULT_COMMAND)[0]

    @property
    def wakeup_command(self) -> str:
        return HARDWARE_COMMAND_DICT.get(self.hardware, DEFAULT_COMMAND)[1]
    
    @classmethod
    def data(cls):
        results = {}
        env_path = Path.home() / ".env"
        load_dotenv(dotenv_path=env_path,verbose=True)
        results["account"] = os.getenv("MI_ACCOUNT")
        results["password"] = os.getenv("MI_PASS")
        return cls(**results)
