from uuid import getnode as get_mac
import redis as redis

import netifaces

redis_db = redis.Redis(host='localhost', port=6379, db=0)
pipe = redis_db.pipeline()

def get_mac_address():
	mac = ':'.join(("%012x" % get_mac())[i:i+2] for i in range(0, 12, 2))
	return mac

def get_mac_addr_by_name(name):
	iface_info = netifaces.ifaddresses('eno1')[netifaces.AF_LINK]
	mac = iface_info[0]["addr"]
	return mac

def main():
	# mac = get_mac_address()
	if_name = netifaces.interfaces()[1]
	mac = get_mac_addr_by_name(if_name)

	print(f'SET SELF:MACADDR {mac}')
	pipe.set("SELF:MACADDR", mac)
	pipe.set("RFDEVICE:STATE", "Idle")

	pipe.execute()
	pass

if __name__ == '__main__':
	main()
