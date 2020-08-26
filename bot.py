import time
import asyncio

from ext.miscellaneous.custom_loger import setup_custom_logger
from ext.modules.botBase import BaseBot
import config

logger = setup_custom_logger(__name__)

loop = asyncio.get_event_loop()
def run_client(token):
	while True:
		ins = BaseBot(prefix="!", description="Custom Discordbot in discord.py")

		try:
			loop.run_until_complete(ins.start(token))
			if ins.ended: break
		except KeyboardInterrupt:
			ins.ended = True
			break
		except Exception as e:
			logger.exception(f"Main Error '''\n{e}'''")
		finally:
			if not ins.ended:
				del ins
				logger.warning("Restarting in 10s...\n")
				time.sleep(10)

if __name__ == '__main__':
	run_client(config.TOKEN)
	loop.close()