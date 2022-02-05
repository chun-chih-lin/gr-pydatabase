import redis as redis
import json

def check_notify(r):
	r.config_set('notify-keyspace-events', 'KEA')
	pass

def redis_setup(db_host='localhost', db_port=6379, db_ch='channel_1', db_idx=0):
	r = redis.Redis(host=db_host, port=db_port, db=db_idx)

	# subprefix = f'__keyevent@{db_idx}__:*'
	subprefix = f'__keyspace@{db_idx}__:Test:*'

	if r.config_get('notify-keyspace-events') != 'KEA':
		# print("set notify-keyspace-events to KEA")
		check_notify(r)
	return r, subprefix
	pass

def utf8_decode(msg):
	return msg.decode("utf-8")

def utf8_len(msg):
	try:
		msg = utf8_decode(msg)
	except:
		pass
	return len(msg)
