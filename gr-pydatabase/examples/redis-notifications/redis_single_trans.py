import numpy as np
import redis as redis
import utils
import time
import json
import random
import string
from time import sleep
from datetime import datetime
import sys

Loop_MAX = 1
# The maximum MSDU is 1500 bytes before encryption.
MSDU_MAX = 100

print(f'len input: {len(sys.argv)}')

input_c = len(sys.argv)

ID = "a"
sleep_bw_pkt = 0.001

if input_c >= 2:
	ID = sys.argv[1]
if input_c >=3:
	sleep_bw_pkt = float(sys.argv[2])
if input_c >=4:
	Loop_MAX=int(sys.argv[3])


r, subprefix = utils.redis_setup(db_host='localhost', db_port=6379, db_ch='channel_1', db_idx=0)

def generate_MSDU(idx):
	print(f'Generating [{idx+1}/{Loop_MAX}] packet...', end='\r')
	MSDU = dict()
	MSDU["idx"] = str(idx)
	MSDU["total"] = str(Loop_MAX)
	MSDU["sequence"] = ID + '.' + str(time.time())
	MSDU["data"] = ""
	MSDU["timestamp"] = str(time.time())
	length_remain = len(json.dumps(MSDU))
	MSDU["data"] = "".join(random.choice(string.ascii_letters) for x in range(MSDU_MAX - length_remain))
	return json.dumps(MSDU, separators=(',', ':'))
	pass

def run_without_pipeline():
	start_time = time.time()
	for x in range(Loop_MAX):
		set_value = generate_MSDU(x)
		# r.set("Trans:"+str(x), set_value)
		action_key = "Single:Trans:"+str(x)
		r.delete(action_key)
		r.set(action_key, set_value)
		r.lpush("QUEUE:LIST:TRANS", action_key)
		sleep(sleep_bw_pkt)
		pass

	print("Total time w/o pipeline: ", time.time()-start_time)
	print("list: ", r.lrange("QUEUE:LIST:TRANS", 0, -1))
	pass

def run_with_pipeline():
	start_time = time.time()
	p = r.pipeline()
	for x in range(Loop_MAX):
		set_value = generate_MSDU(x)
		r.delete("Single:trans")
		r.set("Single:trans", set_value)
		r.lpush("QUEUE:LIST:TRANS", "Single:trans")
	p.execute()
	print("Total time w/ pipeline: ", time.time()-start_time)
	print("list: ", r.smembers("QUEUE:LIST:TRANS"))

def main():
	#r.flushall()
	print("Start transmitting packets...")
	print(f"Rest interval: {sleep_bw_pkt} seconds.")
	print(f"Sequence: {ID}, Total packets: {Loop_MAX}")
	run_without_pipeline()
	# run_with_pipeline()

if __name__ == '__main__':
	main()
