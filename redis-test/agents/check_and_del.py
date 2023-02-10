import redis as redis
import time, sys
import json

pattern = "Recv:*"


if len(sys.argv) > 1:
    print("input with arg")

db = redis.Redis(host='localhost', port=6379, db=0)
if db.keys(pattern):
    print('Something')
    for key in db.keys(pattern):
        print(f"key = {key}")
        if len(sys.argv) >1:
            db.delete(key)
else:
    print('Nothing')
