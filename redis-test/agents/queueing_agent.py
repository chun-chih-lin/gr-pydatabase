import redis as redis
import time
import json
import utils

r, _ = utils.redis_setup()

def event_handler(msg):
	try:
		# key should be 'LISTTEST'
		key = utils.utf8_decode(msg["channel"])
		if key:
			# get the db_key for transmission information
			# db_key = key.split(":")[1]
			db_key = "QUEUE:LIST:TRANS"
			process_message(db_key)
	except Exception as exp:
		print(f'Exception occurs: {exp}')
		pass
	pass

def process_message(db_key):
	while r.exists(db_key):
		rf_device_state = utils.utf8_decode(r.get("RFDEVICE:STATE"))
		if rf_device_state == "Idle":
			# There are some keys in the queue and the RF is Idle.
			oldest_key = utils.utf8_decode(r.lrange(db_key, -1, -1)[0])
			
			# Trigger the Transmission Agent to transmit
			# Set the state of RF as Busy
			p = r.pipeline()
			p.set("TRANSMISSION", oldest_key)
			p.set("RFDEVICE:STATE", "Busy")
			p.execute()
		else:
			print('Still processing, sleep for 1 second.')
			time.sleep(1)
		pass
	pass

def main():
	db_idx = 0
	# Subscribe the 'LISTTEST' pattern
	pubsub = r.pubsub()
	subprefix = f'__keyspace@{db_idx}__:QUEUE:LIST:TRANS'
	pubsub.psubscribe(**{subprefix: event_handler})
	pubsub.run_in_thread(sleep_time=0.01)
	print("Running : worker redis subscriber ...\n=========================================")
	pass

if __name__ == '__main__':
	main()