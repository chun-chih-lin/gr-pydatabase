# https://medium.com/@imamramadhanns/working-with-redis-keyspace-notifications-x-python-c5c6847368a
# https://redis-py.readthedocs.io/en/latest/_modules/redis/client.html#PubSub.run_in_thread

import redis as redis
import utils

r, subprefix = utils.redis_setup(db_host='localhost', db_port=6379, db_ch='channel_1', db_idx=0)

def event_handler(msg):
	print("msg:")
	print(msg)
	try:
		key = utils.utf8_decode(msg["data"])
		if key:
			value = utils.utf8_decode(r.get(key))
			print(key.split(":"))
			print("value: ", value)
			str_length = utils.utf8_len(value)
			print("str_length: ", str_length)
			process_message(value)
	except Exception as exp:
		pass
	pass

def process_message(value):
    # Insert your code below
    print("Processing Message : ", value)

def main():
	pubsub = r.pubsub()
	pubsub.psubscribe(**{subprefix: event_handler})
	pubsub.run_in_thread(sleep_time=0.01)
	print("Running : worker redis subscriber ...")

if __name__ == '__main__':
	main()
