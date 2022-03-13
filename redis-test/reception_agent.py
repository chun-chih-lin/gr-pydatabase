import numpy as np
import redis as redis
import utils
import time
import json
import random
import string

r, subprefix = utils.redis_setup(sub_pattern='RECEPTION')
start_time = time.time()

def event_handler(msg):
	try:
		# key should be 'TRANSMISSION'
		key = utils.utf8_decode(msg["channel"])
		if key:
			# get the db_key for transmission information
			db_key = utils.utf8_decode(r.get("RECEPTION"))
			process_message(db_key)
	except Exception as exp:
		print(f'Exception occurs: {exp}')
		pass
	pass

def process_message(db_key):
	# On receiving the "RECEPTION" key
	# RPOP one element from the QUEUE:LIST:TRANS
	# Once the element is pop from the queueing list,
	# it should trigger the queueing agent to fire another
	# member to be transmitted
	p = r.pipeline()
	p.rpop('QUEUE:LIST:TRANS')
	p.execute()
	pass

def main():
	# Subscribe the 'RECEPTION' pattern
	pubsub = r.pubsub()
	pubsub.psubscribe(**{subprefix: event_handler})
	pubsub.run_in_thread(sleep_time=0.01)
	print("Running : worker redis subscriber ...\n=========================================")
	pass

if __name__ == '__main__':
	main()