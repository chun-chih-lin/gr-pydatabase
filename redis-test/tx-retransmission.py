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

r, subprefix = utils.redis_setup(sub_pattern='SIM_CHANNEL')
start_time = time.time()

src = "10.10.0.1"
dst = "10.10.0.2"

RETRY = 0
packet_loss = 0

def generate_MSDU(idx):
	MSDU = dict()
	MSDU["idx"] = str(idx)
	MSDU["data"] = ""
	MSDU["src"] = src	# Simulate the address for source (itself)
	MSDU["dst"] = dst	# Simulate the address for destination (rx)
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
	# When receive any signal, do:
	# 	First, determine if the packet is for itself.
	# 	Second, if the packet needs an ACK.
	MSPD = json.loads(value)
	if MSPD['dst'] == src:
		# It is for itself
		# Simulate the packet loss rate.
		if random.uniform(0, 1) < 0.95:	
			print(f'Receive a packet.\n\tStore as RECV:{MSPD["idx"]}\r')
			r.set("RECV:" + MSPD["idx"], MSPD["data"])
		else:
			print('Packet loss...\r')
	else:
		# It is for others. Ignore the packet.
		print(f'Receive a packet, but it is not for me.\n\tSource: {MSPD["src"]}\n\tDestination: {MSPD["dst"]}\r')

def monitor_key(trigger_key, trigger_value, pkt_id, sleep_time=0.000010):
	global RETRY
	# Monitor the registered key.
	# If timeout, retransmit again.
	# If reach the maximum retransmit, abort the retransmission.
	recv_key = "RECV:" + pkt_id
	wait_time = 0

	# Used to trigger the retransmission of the packet
	retx_time = 0.0005
	while 1:
		# sleep_time for 10 microseconds
		if r.get(recv_key):
			response = utils.utf8_decode(r.get(recv_key))
			print(f'Receive ACK for packet {pkt_id}. Transmit next pkt.')
			return response
		else:
			time.sleep(sleep_time)
			wait_time = wait_time + sleep_time
		pass

		if wait_time > retx_time:
			wait_time = 0
			print(f'r.get({recv_key}): {r.get(recv_key)}')
			if r.get(recv_key):
				print(r.get(recv_key))
				return
			else:
				print(f'timeout, retransmit count: {RETRY}')
				RETRY += 1
				# Trigger retransmission
				r.set(trigger_key, trigger_value)
				# Delete the key after trigger RF front-end
				r.delete(trigger_key)
	pass

def run_without_pipeline():
	start_time = time.time()
	for x in range(Loop_MAX):
		print('--------------------------------------------------')
		MSDU = generate_MSDU(x)

		trigger_key = "SIM_CHANNEL:CH8"
		trigger_value = MSDU

		# Trigger transmission.
		r.set(trigger_key, trigger_value)
		time.sleep(0.000001)
		# Delete the key after trigger RF front-end
		r.delete(trigger_key)

		# monitor the registered key.
		monitor_key(pkt_id=str(x), trigger_key=trigger_key, trigger_value=trigger_value)
		pass
	print("Total time w/o pipeline: ", time.time()-start_time)
	print(f'Retransmission count: [{RETRY}/{Loop_MAX}]')
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
