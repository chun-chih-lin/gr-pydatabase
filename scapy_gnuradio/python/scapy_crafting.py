import socket
import scapy.all as scapy
import time
import numpy as np

import binascii
import zlib

from uuid import getnode as get_mac


data_frame = scapy.Ether(dst="08:00:27:ce:30:1d")\
	/scapy.IP(dst=["gnuradio.org", "libvolk.org"], ttl=(1,9))\
	/scapy.UDP(sport=12345, dport=52001)/"Hello World!"

beacon_frame = scapy.Dot11FCS(addr1='ff:ff:ff:ff:ff:ff', addr2='23:23:23:23:23:23', addr3='23:23:23:23:23:23')\
	/scapy.Dot11Beacon()/scapy.Dot11Elt(ID='SSID', info='GR WLAN')

fuzz_frame = scapy.Dot11FCS(addr1='ff:ff:ff:ff:ff:ff', addr2='23:23:23:23:23:23', addr3='23:23:23:23:23:23')\
	/scapy.fuzz(scapy.Dot11Beacon()/scapy.Dot11Elt(ID='SSID', info='GR WLAN'))

deauth_frame = scapy.Dot11FCS(addr1='ff:ff:ff:ff:ff:ff', addr2='23:23:23:23:23:23', addr3='23:23:23:23:23:23')\
	/scapy.Dot11Deauth()


ack_frame = scapy.Dot11Ack()

test_frame_1 = scapy.Dot11FCS(addr1='ff:ff:ff:ff:ff:ff', type=1, subtype=13, FCfield=0)
#list(test_frame_1)[0].show()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

test_frame_2 = scapy.Dot11FCS(addr1='ff:ff:ff:ff:ff:ff', type=1, subtype=122, FCfield=0)
#list(beacon_frame)[0].show()


mac = ':'.join(("%012x" % get_mac())[i:i+2] for i in range(0, 12, 2))
ack_frame = scapy.Dot11FCS(addr1=mac, type=1, subtype=13, FCfield=0)

print(f'{ack_frame}')

list(ack_frame)[0].show()
#sock.sendto(bytes(ack_frame), ("127.0.0.1", 52001))

# ==================

data_str = "{\"data\": \"True\", \"Addresses\": {\"SRC\": [0, 0, 0, 0, 0, 0], \"DST\": [1, 1, 1, 1, 1, 255]}}"
b_data_str = data_str.encode("utf-8")
l_data_str = np.array(list(b_data_str), dtype=np.uint8)

data_frame = scapy.Dot11(subtype=0, type=2, addr1='8c:ec:4b:a7:3e:10', addr2='8c:ec:4b:a7:3c:4f', addr3='8c:ec:4b:a7:3e:10')
list(data_frame)[0].show()
print("print data_frame")
b_data_frame = bytes(data_frame)
print(b_data_frame)
l_data_frame = np.array(list(b_data_frame), dtype=np.uint8)
print(type(l_data_frame))
print(type(l_data_frame[0]))
print(l_data_frame)
print(l_data_str)


