
from xiaomibot.migpt import MIGPT
from xiaomusic.config import Device
import libsonic

class XiaoMusicDevice:
    def __init__(self,xiaomusic: MIGPT,device: Device):

        self.xiaomusic = xiaomusic
        self.log = xiaomusic.log
        self.config = xiaomusic.config
        self.device = device
        self.device_id = device.device_id
        
        self.sonic = libsonic.Connection(
            baseUrl = self.config.navidrome_url,
            port = self.config.navidrome_port,
            username= self.config.navidrome_username,
            password= self.config.navidrome_password,
            appName="xiaomibot",
        )

    @property
    def did(self):
        return self.device.did
        
    @property
    def hardware(self):
        return self.device.hardware
    
    def get_cur_music(self):
        return self.device.cur_music
    
    
