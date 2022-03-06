import redis as redis
import utils
import time
import json
import random

r, subprefix = utils.redis_setup(sub_pattern='FROMTX')
start_time = time.time()

def event_handler(msg):
	try:
		key = utils.utf8_decode(msg["channel"])
		split_key = key.split(":")
		db_key = ":".join([i for i in split_key[1:]])
		if db_key:
			value = utils.utf8_decode(r.get(db_key))
			process_message(value)
	except Exception as exp:
		pass
	pass

def process_message(value):
	MSPD = json.loads(value)
	rx_or_not = random.uniform(0, 1)
	print(f'rx_or_not: {rx_or_not}')
	if rx_or_not < 0.95:	
		print('Receive a packet.')
		time.sleep(0.02*random.uniform(0, 1))
		r.set("FROMRX:" + MSPD["idx"], "ACK")
	else:
		print('Packet loss.')

def main():
	pubsub = r.pubsub()
	print(f'subprefix: {subprefix}')
	pubsub.psubscribe(**{subprefix: event_handler})
	pubsub.run_in_thread(sleep_time=0.01)

	rx_or_not = random.uniform(0, 1)
	print(f'rx_or_not: {rx_or_not}')

	print("Running : worker redis subscriber ...\n=========================================")

if __name__ == '__main__':
	main()
