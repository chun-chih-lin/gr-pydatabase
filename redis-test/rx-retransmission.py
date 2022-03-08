import redis as redis
import utils
import time
import json
import random

r, subprefix = utils.redis_setup(sub_pattern='SIM_CHANNEL')
start_time = time.time()

src = "10.10.0.2"
dst = "10.10.0.1"

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
	print("---")
	# When receive any signal, do:
	# 	First, determine if the packet is for itself.
	# 	Second, if the packet needs an ACK.
	MSDU = json.loads(value)
	print(f'MSDU: {type(MSDU)}\n')
	print(MSDU)
	if MSDU['dst'] == src:
		# It is for itself
		# Simulate the packet loss rate.
		if random.uniform(0, 1) < 0.99:
			MSDU['src'] = src
			MSDU['dst'] = dst
			MSDU['data'] = "ACK"
			print('Receive a packet.')
			send_data = json.dumps(MSDU, separators=(',', ':'))
			r.set("SIM_CHANNEL:CH8", send_data)
			time.sleep(0.000001)
			r.delete("SIM_CHANNEL:CH8")

		else:
			print('Packet loss...')
	else:
		# It is for others. Ignore the packet.
		print(f'Receive a packet, but it is not for me.\n\tSource: {MSDU["src"]}\n\tDestination: {MSDU["dst"]}')

def main():
	pubsub = r.pubsub()
	print(f'subprefix: {subprefix}')
	pubsub.psubscribe(**{subprefix: event_handler})
	pubsub.run_in_thread(sleep_time=0.01)
	print("Running : worker redis subscriber ...\n=========================================")

if __name__ == '__main__':
	main()
