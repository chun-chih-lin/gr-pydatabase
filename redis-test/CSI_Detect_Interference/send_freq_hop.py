import redis
import json

db = redis.Redis(host='localhost', port=6379, db=0)

key = f"Trans:FREQ:HOP"
hop_to = 2442000000

ctrl_msg = dict()
ctrl_msg["ControlType"] = "HOP"
ctrl_msg["ControlAction"] = hop_to

json_info = json.dumps(ctrl_msg, separators=(',', ':'))

print(json_info, type(json_info))
db.set(key, json_info)
