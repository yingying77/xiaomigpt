import asyncio
from xiaomibot.config import Config
from xiaomibot.migpt import MIGPT


def main():
    config = Config.data()
    #print(config)
    async def main(config):
        miboy = MIGPT(config)
        try:
            await miboy.run_forever()
        finally:
            await miboy.close()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(config))
