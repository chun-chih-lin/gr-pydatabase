import numpy as np
import redis as redis
import utils
import time
import json
import random
import string
import sys, os

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

		self.MAX_CSI_RECORD = 5

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
			action = self.get_action(msg)
			if action == "CSI":
				csi_key = self.db.get("SYSTEM:ACTION:CSI").decode("utf-8")
				timestamp = csi_key.split(":")[1]
				newest_key = self.db.lrange("SYSTEM:CSI:QUEUE", 0, 0)
				if len(newest_key) < 1:
					self.db.lpush("SYSTEM:CSI:QUEUE", csi_key)
				elif self.is_newer_csi(csi_key, newest_key[0].decode("utf-8")):
					self.db.lpush("SYSTEM:CSI:QUEUE", csi_key)
					if len(self.db.lrange("SYSTEM:CSI:QUEUE", 0, -1)) > self.MAX_CSI_RECORD:
						oldest_csi_key = self.db.rpop("SYSTEM:CSI:QUEUE")
						self.db.delete(oldest_csi_key)
						# We have enough CSI in the Queue, try to detect the interference.
						self.detect_interference()
				else:
					# The key is older somehow. Discard it.
					self.db.delete(csi_key)
			elif action == "DEBUG":
				self.detect_interference()
			else:
				print(f"Other action: {aciton}.")
				
		except Exception as exp:
			e_type, e_obj, e_tb = sys.exc_info()
			print(f'[Action] Exception occurs: {exp}. At line {e_tb.tb_lineno}')
	
	def is_newer_csi(self, coming_key, newest_key):
		return float(coming_key.split(":")[1]) > float(newest_key.split(":")[1])

	def get_action(self, msg):
		return self.utf8_decode(msg['channel']).split(":")[3]

	#--------------------------------------------------------------------------------
	# For Action: Detecting Interference
	def get_all_csi_in_db(self):
		csi_keys_list = self.db.lrange("SYSTEM:CSI:QUEUE", 0, -1)
		csi_list = []
		for csi_key in csi_keys_list:
			csi_json_str = self.db.get(csi_key).decode('utf-8')
			csi_json = json.loads(csi_json_str)
			csi = np.array(csi_json['real']) + 1j*np.array(csi_json['imag'])
			csi_list.append(csi)
		return np.array(csi_list)

	def sliding_var_detect(self, csis):
		sliding_detect_csis = np.zeros((csis.shape[0],csis.shape[1]-self.sliding_window_size))
		for csi_i, csi in enumerate(csis):
			ret = []
			for i, s in enumerate(csi[:len(csi)-self.sliding_window_size]):
				ret.append(np.mean(np.var(csi[i:i+self.sliding_window_size])))

			sliding_detect_csis[csi_i, :] = ret
		return sliding_detect_csis
	
	def median_max_detect(self, sliding_var_ary):
		median_max_detection = []

		for d_i, d in enumerate(sliding_var_ary):
			median = np.median(d)
			max_v = np.max(d)
			if median == 0:
				median_max_detection.append(0)
			elif max_v/median > self.median_threshold:
				median_max_detection.append(1)
			else:
				median_max_detection.append(0)
		return median_max_detection

	def consecutive_detect(self, detections):
		consecutive_detection = [a*b for (a, b) in zip(detections[:-1], detections[2:])]
		return consecutive_detection


	def detect_interference(self):
		print('[Action] Detecting interference...')

		# TODO: Setting should be set in db for dynamic changes
		self.sliding_window_size = 4
		self.median_threshold = 5.0

		FAILRED = '\033[91m'
		OKGREEN = '\033[92m'
		WARNING = '\033[93m'
		EOC = '\033[0m'
		csi_list = self.get_all_csi_in_db()

		sliding_var_detect_csis = self.sliding_var_detect(csi_list)
		detections = self.median_max_detect(sliding_var_detect_csis)
		consecutive_detection = self.consecutive_detect(detections)
		print(f'consecutive_detection: {consecutive_detection}')

		

		
		



def main():
	print('Running Action Agent...')
	ActionAgent('SYSTEM:ACTION:*', 'AGENT:ACTION')

if __name__ == "__main__":
	main()
