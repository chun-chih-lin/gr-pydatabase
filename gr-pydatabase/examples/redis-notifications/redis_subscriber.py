# https://medium.com/@imamramadhanns/working-with-redis-keyspace-notifications-x-python-c5c6847368a
# https://redis-py.readthedocs.io/en/latest/_modules/redis/client.html#PubSub.run_in_thread

import redis as redis
import utils
import time

r, subprefix = utils.redis_setup(db_host='localhost', db_port=6379, db_ch='channel_1', db_idx=0)
start_time = time.time()
def event_handler(msg):
	try:
		key = utils.utf8_decode(msg["channel"])
		split_key = key.split(":")
		db_key = ":".join([i for i in split_key[1:]])
		if db_key:
			value = utils.utf8_decode(r.get(db_key))
			str_length = utils.utf8_len(value)
			process_message(value)
			if int(value) == 0:
				start_time = time.time()
			elif int(value) == 9999:
				print("Total time: ", time.time()-start_time)
	except Exception as exp:
		pass
	pass

def process_message(value):
	# Insert your code below
	r.set("Recv:" + str(value), value)

def main():
	pubsub = r.pubsub()
	# print("subprefix: ", subprefix)
	pubsub.psubscribe(**{subprefix: event_handler})
	pubsub.run_in_thread(sleep_time=0.01)
	# print("Running : worker redis subscriber ...")

if __name__ == '__main__':
	main()
