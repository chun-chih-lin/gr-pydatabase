import numpy as np
import redis as redis
import utils
import time
import json
import random
import string

Loop_MAX = 100
# The maximum MSDU is 1500 bytes before encryption.
MSDU_MAX = 10
RETRY_MAX = 5
WAIT_MAX = 0.001

r, subprefix = utils.redis_setup(sub_pattern='TRANSMISSION')
start_time = time.time()

def event_handler(msg):
	try:
		# key should be 'TRANSMISSION'
		key = utils.utf8_decode(msg["channel"])
		if key:
			# get the db_key for transmission information
			db_key = utils.utf8_decode(r.get("TRANSMISSION"))
			process_message(db_key)
	except Exception as exp:
		print(f'Exception occurs: {exp}')
		pass
	pass

def check_rf_state():
	if utils.utf8_decode(r.get("RFDEVICE:STATE")) == "Busy":
		pass
	else:
		r.set("RFDEVICE:STATE", "Busy")

def process_message(db_key):
	check_rf_state()
	db_value = utils.utf8_decode(r.get(db_key))

	# Trigger RF front-end to transmit the data
	r.set(f'Trans:{db_key}', db_value)

	# Monitor the key and retransmit if needed
	monitor_key(db_key=db_key)
	pass

def monitor_key(db_key):
	global RETRY_MAX
	global WAIT_MAX
	key_ack = f'{db_key}:ACK'

	retry_count = 0
	waiting_time = 0.0
	waiting_interval = 0.0001

	while retry_count < RETRY_MAX:
		if r.exists(key_ack):
			# It must receive the ACK
			return
		elif waiting_time <= WAIT_MAX:
			# Haven't received the ACK yet, and not timeout yet.
			time.sleep(waiting_interval)
			waiting_time += waiting_interval
		else:
			# Haven't received the ACK and timeout occurs.
			retry_count += 1
			waiting_time = 0.0
			p = r.pipeline()
			p.delete(f'Trans:{db_key}')
			p.set(f'Trans:{db_key}', db_value)
			p.execute()
		pass
	pass
	# Outside the while indicates the retry max is researched.
	# Report Failed
	p = r.pipeline()
	p.set("RECEPTION", db_key)
	p.set(key_ack, "Failed")
	p.set("RFDEVICE:STATE", "Idle")
	p.execute()

def main():
	# Subscribe the 'TRANSMISSION' pattern
	pubsub = r.pubsub()
	pubsub.psubscribe(**{subprefix: event_handler})
	pubsub.run_in_thread(sleep_time=0.01)
	print("Running : worker redis subscriber ...\n=========================================")
	pass

if __name__ == '__main__':
	main()