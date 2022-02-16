import numpy as np
import redis as redis
import utils
import time
import json
import random
import string

Loop_MAX = 1
# The maximum MSDU is 1500 bytes before encryption.
MSDU_MAX = 1000

r, subprefix = utils.redis_setup(db_host='localhost', db_port=6379, db_ch='channel_1', db_idx=0)

def generate_MSDU(idx):
	MSDU = dict()
	MSDU["idx"] = str(idx)
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
	r.flushall()
	run_without_pipeline()
	# run_with_pipeline()

if __name__ == '__main__':
	main()
