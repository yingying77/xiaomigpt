from dataclasses import dataclass

from xiaomusic.const import PLAY_TYPE_RND


@dataclass
class Device:
    did: str = ""
    device_id: str = ""
    hardware: str = ""
    name: str = ""
    play_type: int = PLAY_TYPE_RND
    cur_music: str = ""
    cur_playlist: str = ""