import redis as redis
import time
import json

pattern = "Recv:a.1647915582.241072*"

db = redis.Redis(host='localhost', port=6379, db=0)
if db.keys(pattern):
	print('Something')
else:
	print('Nothing')
