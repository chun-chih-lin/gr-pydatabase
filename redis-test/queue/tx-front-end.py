import redis as redis
import time
import json
import utils

MSDU_MAX = 10
RETRY_MAX = 5

src = "10.10.0.1"
dst = "10.10.0.2"
# set retransmission timeout for 1ms
TIMEOUT = 0.001

r, subprefix = utils.redis_setup()

# -------------------------------------------------------------------------------

def tx_event_handler(msg):
	try:
		# key should be 'TRANSMISSION'
		key = utils.utf8_decode(msg["channel"])
		prinf(f'[TX Event] key: {key}')
		if key:
			# get the db_key for transmission information
			db_key = utils.utf8_decode(r.get(key))
			process_message(db_key)
	except Exception as exp:
		print(f'Exception occurs: {exp}')
		pass
	pass

def process_message(db_key):
	# get db_key for the transmission details
	value = utils.utf8_decode(r.get(db_key))
	# Trigger GNURadio and RF front-end to transmit the data.
	r.set("TRANS:" + db_key, value)
	monitor_key(retx_key="TRANS:" + db_key, retx_value=value, db_key=db_key)

def monitor_key(retx_key, retx_value, db_key):
	# Delete the trigger key
	r.delete(retx_key)

	global RETRY_MAX
	global TIMEOUT
	# retx_key: the key used for triggering GNURadio to retransmit
	# retx_value: the value used for transmission
	# db_key: the value of the db_key itself
	monitor_interval=0.000010
	monitor_ack = f'{db_key}:ACK'
	monitor_time = 0
	retry_count = 0
	while not r.exist(monitor_ack):
		# If the {db_key}:ACK is not exist, keep monitoring the key.
		if monitor_time >= TIMEOUT:
			if retry_count >= RETRY_MAX:
				# Timeout, and exceeding the maximum retry count.
				# Report Failed.
				p = r.pipeline()
				p.set("RECEPTION", db_key)			# Trigger recption
				p.set("RFDEVICE:STATE", "Idle")		# Set RF device's state as Idle
				p.set(monitor_ack, "Failed")		# Report the transmission status
				p.execute()
			else:
				# Timeout, need retransmission
				r.set(retx_key, retx_value)
				retry_count += 1
				monitor_time = 0
				r.delete(retx_key)
		else:
			# monitor every monitor_interval seconds
			time.sleep(monitor_interval)
			monitor_time += monitor_interval
		pass
	pass

def rx_event_handler(msg):
	# GNURadio should determine is the received message is for this device.
	# Everything comes to this point MUST be sent to this device.
	try:
		# key should be 'RECEPTION'
		key = utils.utf8_decode(msg["channel"])
		prinf(f'[RX Event] key: {key}')
		if key:
			# get the db_key for transmission information
			db_key = utils.utf8_decode(r.get(key))
			process_receiving_message(db_key)
	except Exception as exp:
		print(f'Exception occurs: {exp}')
		pass
	pass

def process_receiving_message(db_key):
	# db_key = utils.utf8_decode(r.get(db_key))
	p = r.pipeline()
	p.set("RFDEVICE:STATE", "Idle")		# Set RF device's state as Idle
	p.set(monitor_ack, "Succ")			# Report the transmission status
	p.delete(f'RECV:{db_key}')
	p.execute()
	pass

# -------------------------------------------------------------------------------

def main():
	# Subscribe the 'TRANSMISSION' pattern
	pubsub = r.pubsub()
	subprefix_1 = f'__keyspace@{db_idx}__:TRANSMISSION:*'
	subprefix_2 = f'__keyspace@{db_idx}__:RECEPTION:*'
	pubsub.psubscribe(**{subprefix_1: tx_event_handler})
	pubsub.psubscribe(**{subprefix_2: rx_event_handler})
	pubsub.run_in_thread(sleep_time=0.01)
	print("Running : worker redis subscriber ...\n=========================================")
	pass

if __name__ == '__main__':
	main()