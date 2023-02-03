import numpy as np
import redis as redis
import utils
import time
import json
import random
import string

class TransAgent(object):
	"""docstring for TransAgent"""
	def __init__(self, subprefix, agentkey):
		super(TransAgent, self).__init__()
		print('Initialing TransAgent...')
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

		self.RETRY_MAX = 5
		self.WAIT_MAX = 0.01
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
		return msg.decode("utf-8")

	def check_rf_state(self, state):
		if self.utf8_decode(self.db.get(self.REDEVICE_STATE)) == state:
			pass
		else:
			self.db.set(self.REDEVICE_STATE, state)

	def agent_event_handler(self, msg):
		try:
			key = self.utf8_decode(msg["channel"])
			if key:
				db_key = self.utf8_decode(self.db.get(self.agentkey))
				if db_key == self.KEYWORD_QUIT:
					print('Quiting TransAgent. See you again.')
					self.db.set('AGENT:TRANS', self.KEYWORD_STOP)
					self.thread.stop()
		except Exception as exp:
			print(f'[Trans] Exception occurs: {exp}')
		pass

	def event_handler(self, msg):
		try:
			print(f'[Trans] Event! {msg}')
			# key should be 'TRANSMISSION'
			key = self.utf8_decode(msg["channel"])
			if key:
				# get the db_key for transmission information
				db_key = self.utf8_decode(self.db.get(self.subprefix))
				self.process_message(db_key)
		except Exception as exp:
			print(f'[Trans] Exception occurs: {exp}')
			pass
		pass

	def process_message(self, db_key):
		self.check_rf_state(state=self.KEYWORD_BUSY)
		PMDU_msg = self.utf8_decode(self.db.get(db_key))

		# Trigger RF front-end to transmit the data
		# Add the key into waiting ACK list.
		p = self.db.pipeline()
		# Trigger the RF front-end to transmit
		print(f'=================== Transmitting Trans:{db_key}...')
		p.set(f'Trans:{db_key}', PMDU_msg)
		p.set(self.MONITOR_ACK, self.ACK_STATE_WAIT)
		p.execute()

		# Monitor the key and retransmit if needed
		self.monitor_key(db_key=db_key, PMDU_msg=PMDU_msg)
		pass

	def monitor_key(self, db_key, PMDU_msg):
		print(f'[Trans Agent] Start monitoring...')
		key_ack = f'{db_key}:ACK'

		retry_count = 0
		waiting_time = 0.0
		waiting_interval = 0.001

		while retry_count < self.RETRY_MAX:
			if self.db.get(self.SYSTEM_STATE).decode('utf-8') == self.SYSTEM_TRANS_HOLD:
				print('System holds')
				time.sleep(0.01)
			elif self.db.get(self.MONITOR_ACK).decode("utf-8") != self.ACK_STATE_WAIT:
				print(f'[Trans Agent] {self.db.get(self.MONITOR_ACK).decode("utf-8")}')
				# It must receive the ACK
				return
			elif waiting_time <= self.WAIT_MAX:
				print(f'[Trans Agent] {self.db.get(self.MONITOR_ACK).decode("utf-8")}, {waiting_time} < {self.WAIT_MAX}, not timeout.')
				# Haven't received the ACK yet, and not timeout yet.
				time.sleep(waiting_interval)
				waiting_time += waiting_interval
			else:
				# Haven't received the ACK and timeout occurs.
				print(f'[Trans Agent] Timeout. Retry [{retry_count+1}/{self.RETRY_MAX}]')
				retry_count += 1
				waiting_time = 0.0
				p = self.db.pipeline()
				p.delete(f'Trans:{db_key}')
				p.set(f'Trans:{db_key}', PMDU_msg)
				p.execute()
			pass
		pass
		# Outside the while indicates the retry max is researched.
		# Report Failed
		self.abort_monitor(db_key, key_ack)
	
	def abort_monitor(self, db_key, key_ack):
		print(f'[Trans Agent] ACK status: {self.db.get(self.MONITOR_ACK).decode("utf-8")}, Abort monitoring...')
		p = self.db.pipeline()
		p.set("RECEPTION", db_key)
		p.set(key_ack, "Failed")
		p.set(self.REDEVICE_STATE, self.KEYWORD_IDLE)
		p.set(self.MONITOR_ACK, self.ACK_STATE_FAIL)
		p.rpop('QUEUE:LIST:TRANS')
		p.execute()
		pass

def main():
	print('Running Transmission Agent...')
	TransAgent('TRANSMISSION', 'AGENT:TRANS')
	pass

if __name__ == '__main__':
	main()	
