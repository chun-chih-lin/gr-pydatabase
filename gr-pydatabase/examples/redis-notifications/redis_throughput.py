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

Loop_MAX = 100
# The maximum MSDU is 1500 bytes before encryption.
MSDU_MAX = 100

ID = 'a'
sleep_bw_pkt = 0.01

print(len(sys.argv))

if len(sys.argv) >= 2:
	ID = sys.argv[1]
if len(sys.argv) == 3:
	sleep_bw_pkt = float(sys.argv[2])

print(f'Throughput test with sequence name: {ID}, interval: {sleep_bw_pkt}')

r, subprefix = utils.redis_setup(db_host='localhost', db_port=6379, db_ch='channel_1', db_idx=0)

def generate_MSDU(idx):
	print(f'Generating [{idx+1}/{Loop_MAX}] packet...', end='\r')
	MSDU = dict()
	MSDU["idx"] = str(idx)
	MSDU["total"] = str(Loop_MAX)
	MSDU["sequence"] = ID
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
		r.set("Trans:"+str(x), set_value)
		sleep(sleep_bw_pkt)
		pass

	print("Total time w/o pipeline: ", time.time()-start_time)
	pass

def run_with_pipeline():
	start_time = time.time()
	p = r.pipeline()
	for x in range(Loop_MAX):
		set_value = generate_MSDU(x)
		p.set("Trans:"+str(x), set_value)
	p.execute()
	print("Total time w/ pipeline: ", time.time()-start_time)

def main():
	print("Start transmitting packets...")
	print(f"Rest interval: {sleep_bw_pkt} seconds.")
	print(f"Sequence: {ID}, Total packets: {Loop_MAX}")
	run_without_pipeline()
	# run_with_pipeline()

if __name__ == '__main__':
	main()
