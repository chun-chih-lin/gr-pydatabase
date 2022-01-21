import redis as redis

def check_notify(r):
	r.config_set('notify-keyspace-events', 'KEA')
	pass

def redis_setup(db_host='localhost', db_port=6379, db_ch='channel_1', db_idx=0):
	r = redis.Redis(host=db_host, port=db_port, db=db_idx)
	if r.config_get('notify-keyspace-events') != 'KEA':
		print("set notify-keyspace-events to KEA")
		check_notify(r)
	return r, db_ch
	pass