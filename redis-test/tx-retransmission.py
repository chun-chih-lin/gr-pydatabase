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

r, subprefix = utils.redis_setup(sub_pattern='FROMRX')
start_time = time.time()

def generate_MSDU(idx):
	MSDU = dict()
	MSDU["idx"] = str(idx)
	MSDU["data"] = ""
	MSDU["timestamp"] = str(time.time())
	length_remain = len(json.dumps(MSDU))
	MSDU["data"] = "".join(random.choice(string.ascii_letters) for x in range(MSDU_MAX - length_remain))
	return json.dumps(MSDU, separators=(',', ':'))
	pass

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
	if rx_or_not < 0.7:	
		print('Receive a packet.')
		r.set("FROMTX:" + MSPD["idx"], MSPD["data"])
	else:
		print('Packet loss.')

def monitor_key(mon_key, tx_key, tx_value, pkt_id, sleep_time=0.01):
	wait_time = 0
	retx_time = 0.02
	while 1:
		
		if r.get(mon_key+pkt_id):
			response = utils.utf8_decode(r.get(mon_key+pkt_id))
			print(f'Receive ACK for packet {pkt_id}. Transmit next pkt.')
			return response
		else:
			time.sleep(sleep_time)
			wait_time = wait_time + sleep_time
		pass

		if wait_time >= retx_time:
			wait_time = 0
			print(f'timeout, transmit')
			# Retransmission
			r.set(tx_key+pkt_id, tx_value)
	pass

def run_without_pipeline():
	start_time = time.time()
	for x in range(Loop_MAX):
		set_value = generate_MSDU(x)
		r.set("FROMTX:"+str(x), set_value)
		monitor_key(mon_key="FROMRX:", tx_key="FROMTX:", pkt_id=str(x), tx_value=set_value)
		pass
	print("Total time w/o pipeline: ", time.time()-start_time)
	pass

def main():
	r.flushall()
	pubsub = r.pubsub()
	print(f'subprefix: {subprefix}')
	pubsub.psubscribe(**{subprefix: event_handler})
	pubsub.run_in_thread(sleep_time=0.01)
	print("Running : worker redis subscriber ...\n=========================================")

	run_without_pipeline()

if __name__ == '__main__':
	main()
