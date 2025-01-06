import asyncio
from xiaomibot.migpt import MIGPT
from xiaomibot.config import Config
if __name__ == "__main__":
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
