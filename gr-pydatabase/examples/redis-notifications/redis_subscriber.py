# https://medium.com/@imamramadhanns/working-with-redis-keyspace-notifications-x-python-c5c6847368a
# https://redis-py.readthedocs.io/en/latest/_modules/redis/client.html#PubSub.run_in_thread

import redis as redis
import utils

r, db_ch = utils.redis_setup()

def event_handler(msg):
	try:
		key = msg["data"].decode("utf-8")
		if key:
			# key = key.replace("valKey:", "")
			value = r.get(key)
			process_message(value)
	except Exception as exp:
		pass
	pass

def process_message(value):
    # Insert your code below
    print("Processing Message : ", value)

def main():
	pubsub = r.pubsub()
	pubsub.psubscribe(**{'__keyevent@0__:*': event_handler})

	print('Starting message loop')

	pubsub.run_in_thread(sleep_time=0.01)
	print("Running : worker redis subscriber ...")

if __name__ == '__main__':
	main()