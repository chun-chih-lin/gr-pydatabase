import numpy as np
import redis as redis
import utils
import time
import json
import random
import string

class ActionAgent(object):
	def __init__(self, subprefix, agentkey):
		super(ActionAgent, self).__init__()
		print('Initialing ActionAgent...')
		self.db_host = 'localhost'
		self.db_port = 6379
		self.db_idx = 0
		self.subprefix = subprefix
		self.agentkey = agentkey

		self.db = redis.Redis(host=self.db_host, port=self.db_port, db=self.db_idx)
		self.subpattern = f'__keyspace@{self.db_idx}__:{self.subprefix}'
		self.agentpattern = f'__keyspace@{self.db_idx}__:{self.agentkey}'

		self.check_notify()

		self.pubsub = self.db.pubsub()
		self.pubsub.psubscribe(**{self.subpattern: self.event_handler})
		self.pubsub.psubscribe(**{self.agentpattern: self.agent_event_handler})
		self.thread = self.pubsub.run_in_thread(sleep_time=0.001)

		self.REDEVICE_STATE = "RFDEVICE:STATE"
		self.MONITOR_ACK = "TRANS:ACK"
		self.ACK_STATE_WAIT = "Waiting"
		self.ACK_STATE_FAIL = "Failed"
		self.ACK_STATE_SUCC = "Success"

		self.KEYWORD_QUIT = "Quit"
		self.KEYWORD_BUSY = "Busy"
		self.KEYWORD_IDLE = "Idle"
		self.KEYWORD_STOP = "Stop"
		self.KEYWORD_WAIT_ACK = "WAITACK"

		self.SYSTEM_STATE = "RFSYSTEM:STATE"
		self.SYSTEM_FREE = "Free"
		self.SYSTEM_TRANS_HOLD = "Hold"

		print('Initialization done.')
	
	def check_notify(self):
		self.db.config_set('notify-keyspace-events', 'KEA')
		pass
	
	def utf8_decode(self, msg):
		return msg.decode('utf-8')
	
	def agent_event_handler(self, msg):
		try:
			key = self.utf8_decode(msg['channel'])
			if key:
				db_key = self.utf8_decode(self.db.get(self.agentkey))
				if db_key == self.KEYWORD_QUIT:
					print('Quiting ActionAgent. See you again.')
					self.db.set('AGENT:ACTION', self.KEYWORD_STOP)
					self.thread.stop()
		except Exception as exp:
			print(f'[Action] Exception occurs: {exp}')

	def event_handler(self, msg):
		try:
			print(f'[Action] Event! {msg}')

		except Exception as exp:
			print(f'[Action] Exception occurs: {exp}')


def main():
	print('Running Action Agent...')
	ActionAgent('ACTION', 'AGENT:ACTION')

if __name__ == "__main__":
	main()
