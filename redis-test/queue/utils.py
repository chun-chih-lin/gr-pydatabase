import redis as redis
import json

def check_notify(r):
	r.config_set('notify-keyspace-events', 'KEA')
	pass

def redis_setup(db_host='localhost', db_port=6379, db_ch='channel_1', db_idx=0, sub_pattern='Test'):
	r = redis.Redis(host=db_host, port=db_port, db=db_idx)
	subprefix = f'__keyspace@{db_idx}__:{sub_pattern}:*'

	if r.config_get('notify-keyspace-events') != 'KEA':
		check_notify(r)
	return r, subprefix
	pass

# def utf8_decode(msg):
# 	return msg.decode("utf-8")

def utf8_len(msg):
	try:
		msg = utf8_decode(msg)
	except:
		pass
	return len(msg)

def utf8_decode(l):
    if isinstance(l, list):
        return [decode(x) for x in l]
    else:
        return l.decode('utf-8')