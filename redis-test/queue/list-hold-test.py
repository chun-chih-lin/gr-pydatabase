import redis as redis
import time
import json
import utils

r, subprefix = utils.redis_setup()

def event_handler(msg):
	try:
		# key should be 'LISTTEST'
		key = utils.utf8_decode(msg["channel"])
		if key:
			# get the db_key for transmission information
			db_key = key.split(":")[1]
			process_message(db_key)
	except Exception as exp:
		print(f'Exception occurs: {exp}')
		pass
	pass

def process_message(db_key):
	while r.exists(db_key):
		pop_value = utils.utf8_decode(r.rpop(db_key))
		print(f'RPOP value: {pop_value}')
		print('sleep for 2 second.')
		time.sleep(2)
		pass
	pass

def main():
	db_idx = 0
	# Subscribe the 'LISTTEST' pattern
	pubsub = r.pubsub()
	subprefix = f'__keyspace@{db_idx}__:LISTTEST'
	pubsub.psubscribe(**{subprefix: event_handler})
	pubsub.run_in_thread(sleep_time=0.01)
	print("Running : worker redis subscriber ...\n=========================================")
	pass

if __name__ == '__main__':
	main()