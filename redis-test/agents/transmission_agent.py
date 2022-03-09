import numpy as np
import redis as redis
import utils
import time
import json
import random
import string

class TransAgent(object):
	"""docstring for TransAgent"""
	def __init__(self, subprefix):
		super(TransAgent, self).__init__()
		print('Initialing TransAgent...')
		self.db_host = 'localhost'
		self.db_port = 6379
		self.db_idx = 0
		self.subprefix = subprefix

		self.db = redis.Redis(host=self.db_host, port=self.db_port, db=self.db_idx)
		self.subpattern = f'__keyspace@{self.db_idx}__:{self.subprefix}'

		self.check_notify()

		self.pubsub = self.db.pubsub()
		self.pubsub.psubscribe(**{self.subpattern: self.event_handler})
		self.thread = self.pubsub.run_in_thread(sleep_time=0.01)

		self.RETRY_MAX = 5
		self.WAIT_MAX = 0.001
		self.REDEVICE_STATE = "RFDEVICE:STATE"

		self.KEYWORD_QUIT = "Quit"
		self.KEYWORD_BUSY = "Busy"
		self.KEYWORD_IDLE = "Idle"
		self.KEYWORD_WAIT_ACK = "WAITACK"
		print('Initialization done.')

	def check_notify(self):
		self.db.config_set('notify-keyspace-events', 'KEA')
		pass

	def utf8_decode(self, msg):
		return msg.decode("utf-8")

	def check_rf_state(self, state):
		if self.utf8_decode(self.db.get(self.REDEVICE_STATE)) == state:
			pass
		else:
			self.db.set(self.REDEVICE_STATE, state)

	def event_handler(self, msg):
		try:
			# key should be 'TRANSMISSION'
			key = self.utf8_decode(msg["channel"])
			if key:
				# get the db_key for transmission information
				db_key = self.utf8_decode(self.db.get(self.subprefix))
				if db_key == self.KEYWORD_QUIT:
					print('Quiting TransAgent. See you again.')
					self.thread.stop()
				else:
					self.process_message(db_key)
		except Exception as exp:
			print(f'Exception occurs: {exp}')
			pass
		pass

	def process_message(self, db_key):
		self.check_rf_state(state=self.KEYWORD_BUSY)
		db_value = self.utf8_decode(self.db.get(db_key))

		# Trigger RF front-end to transmit the data
		# Add the key into waiting ACK list.
		p = self.db.pipeline()
		p.set(f'Trans:{db_key}', db_value)
		p.sadd(self.KEYWORD_WAIT_ACK, db_key)
		p.execute()

		# Monitor the key and retransmit if needed
		self.monitor_key(db_key=db_key)
		pass

	def monitor_key(self, db_key):
		key_ack = f'{db_key}:ACK'

		retry_count = 0
		waiting_time = 0.0
		waiting_interval = 0.0001

		while retry_count < self.RETRY_MAX:
			if self.db.exists(key_ack):
				# It must receive the ACK
				return
			elif waiting_time <= self.WAIT_MAX:
				# Haven't received the ACK yet, and not timeout yet.
				time.sleep(waiting_interval)
				waiting_time += waiting_interval
			else:
				# Haven't received the ACK and timeout occurs.
				retry_count += 1
				waiting_time = 0.0
				p = self.db.pipeline()
				p.delete(f'Trans:{db_key}')
				p.set(f'Trans:{db_key}', db_value)
				p.sadd(self.KEYWORD_WAIT_ACK, db_key)
				p.execute()
			pass
		pass
		# Outside the while indicates the retry max is researched.
		# Report Failed
		p = self.db.pipeline()
		p.set("RECEPTION", db_key)
		p.set(key_ack, "Failed")
		p.srem(self.KEYWORD_WAIT_ACK, db_key)
		p.set(self.REDEVICE_STATE, self.KEYWORD_IDLE)
		p.execute()

def main():
	print('Running Transmission Agent...')
	TransAgent('TRANSMISSION')
	pass

if __name__ == '__main__':
	main()	