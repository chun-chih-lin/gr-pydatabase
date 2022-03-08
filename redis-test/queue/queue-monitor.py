import numpy as np
import redis as redis
import utils
import time
import json
import random
import string

r, subprefix = utils.redis_setup(sub_pattern='MONITOR')

def decode(l):
    if isinstance(l, list):
        return [decode(x) for x in l]
    else:
        return l.decode('utf-8')

def event_handler(msg):
	try:
		key = utils.utf8_decode(msg["channel"])
		split_key = key.split(":")
		db_key = ":".join([i for i in split_key[1:]])
		if db_key:
			process_event(db_key)
	except Exception as exp:
		print(f'Exception: {exp}')
		pass
	pass

def process_event(db_key):
	# type: ['string', 'list', 'set', 'zset', 'hash', 'stream']
	key_type = r.type(db_key)
	if decode(key_type) == 'zset':
		value = decode(r.zrange(db_key, 0, -1))
		print(f'Event trigger: key: {db_key}, value: {value}, type: {key_type}')
		print(value)
	else:
		print(f'Wrong key type. Is "{key_type}", instead of "zset".')
		pass
	pass

def main():
	pubsub = r.pubsub()
	print("subprefix: ", subprefix)
	pubsub.psubscribe(**{subprefix: event_handler})
	pubsub.run_in_thread(sleep_time=0.01)
	pass

if __name__ == '__main__':
	main()