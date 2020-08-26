import logging
import coloredlogs
from config import LOGLEVEL, LOG_FILE

logging.getLogger('discord').setLevel(logging.WARNING)
logging.getLogger('youtube_dl').setLevel(logging.CRITICAL)
logging.getLogger('asyncio').setLevel(logging.CRITICAL)

formater = logging.Formatter(fmt="%(asctime)s %(name)s %(levelname)s %(message)s", datefmt='%d-%m-%Y %H:%M:%S')

fh = logging.FileHandler(LOG_FILE)
fh.setLevel(logging.WARNING)
fh.setFormatter(formater)

def setup_custom_logger(name, override_log_level=None):
	logger = logging.getLogger(name)
	logger.addHandler(fh)

	if not override_log_level:
		coloredlogs.install(level=LOGLEVEL, logger=logger)
	else:
		coloredlogs.install(level=override_log_level, logger=logger)

	return logger
