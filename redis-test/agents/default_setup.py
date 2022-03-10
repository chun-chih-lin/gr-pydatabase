from uuid import getnode as get_mac
import redis as redis

redis_db = redis.Redis(host='localhost', port=6379, db=0)
pipe = redis_db.pipeline()

def get_mac_address():
	mac = ':'.join(("%012x" % get_mac())[i:i+2] for i in range(0, 12, 2))
	return mac

def main():
	mac = get_mac_address()

	print(f'SET SELF:MACADDR {mac}')
	pipe.set("SELF:MACADDR", mac)

	pipe.execute()
	pass

if __name__ == '__main__':
	main()