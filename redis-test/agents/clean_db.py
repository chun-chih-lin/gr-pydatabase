import redis as redis
import time
import json
import sys

db = redis.Redis(host='localhost', db=0, port=6379)
prefix = "Recv:"

if len(sys.argv) >=2:
	prefix = sys.argc[1]

print(f'Delete prefix: {prefix}')


def main():
	print(f'key pattern: {prefix+"*"}')
	all_keys = db.keys(prefix+'*')

	for i, key in enumerate(all_keys):
		print(f'processing for key: {key.decode("utf-8")}')
		db.delete(key)

if __name__ == '__main__':
	main()
