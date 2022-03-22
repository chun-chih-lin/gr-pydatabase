import logging
import logging.handlers
import optparse
import os, sys
import redis as redis

db = redis.Redis(host='localhost', port=6379, db=0)

LOG_LEVELS = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET']
LOG_DIRECTORY = '/var/log/wifi.log'

def init():
	log_level = "INFO"
	try:
		log_level = db.get("SYS:LOG_LEVEL").decode("utf-8")
		print('success')
	except Exception as e:
		pass

	if log_level.upper() in LOG_LEVELS:
		log_level = log_level.upper()
	else:
		log_level = "INFO"
	
	formatter = '[%(asctime)s] [%(levelname)s] %(message)s'
	logging.basicConfig(level=log_level, filename=LOG_DIRECTORY, format=formatter)
	logger = logging.getLogger()
	return logger


def main():
	logger = init()

	logger.debug('debug message')
	logger.info('info message')
	logger.warn('warn message')
	logger.error('error message')
	logger.critical('critical message')

	pass

if __name__ == '__main__':
	main()