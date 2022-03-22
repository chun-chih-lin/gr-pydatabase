import redis as redis
import time
import json

db = redis.Redis(host='localhost', port=6379, db=0)

def evaluation(db_keys):
	for i, key in enumerate(db_keys):
		hash_value = db.hgetall(key)
		try:
			payload = json.loads(hash_value[b'payload'])
			seq = payload['sequence']
			print(f'key: {key.decode("utf-8")}, seq: {seq}')
		except Exception as e:
			print(f'Exception: {e}')

def main():
	all_keys = db.keys('Recv:*')
	print(f'all_keys, type: {type(all_keys)}')
	evaluation(all_keys)
	pass

if __name__ == '__main__':
	main()
