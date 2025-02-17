import requests
import cn2an
import re
import os
import logging
class HASS:
    def __init__(self):
        self.url = os.getenv("HASS_URL")
        self.token = os.getenv("HASS_TOKEN")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "content-type": "application/json",
            }
        self.log = logging.getLogger("hass")
    def _cn2an(self,text:str):
        regx = "[一二三四五六七八九十]?[千]?[一二三四五六七八九十]?[百]?[一二三四五六七八九十]?[十]?[一二三四五六七八九十]?"
        res = re.findall(regx,text)
        res = [x for x in res if x != ""]
        result = text
        for i in res:
            result = result.replace(i,str(cn2an.cn2an(i)))
        self.log.info(result)
        return result

    def ask(self, intent: str):
        url = f"{self.url}/api/conversation/process"
        data = {         
            "text": self._cn2an(intent),
            "language": "zh-CN",
            }
        response = requests.post(url=url, headers=self.headers, json=data)
        self.log.info(f"get:{url},data:{data}")
        self.log.info(response)
        try:
            speech = response.json().get("response").get("speech",{}).get("plain",{}).get("speech",{})
            return speech
        except:
            self.log.info("hass error")
        return None
    
if __name__ == "__main__":
    hass = HASS()
    hass._cn2an("鱼缸灯亮度一百")
    #response = hass.ask("客厅温度是多少？")
    #print(json.dumps(response, indent=4, ensure_ascii=False))
