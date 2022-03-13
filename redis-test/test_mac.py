import pmt
import numpy
from gnuradio import gr
import socket
import scapy.all as scapy
from uuid import getnode as get_mac

mac = ':'.join(("%012x" % get_mac())[i:i+2] for i in range(0, 12, 2))
ack_frame = scapy.Dot11FCS(addr1=mac, type=1, subtype=13, FCfield=0)
# list(ack_frame)[0].show()

byte_frame = bytes(ack_frame)

print(byte_frame)
print(type(byte_frame))

# str_msg = pmt.to_python(pmt.cdr(byte_frame))
# print(str_msg)


msdu = numpy.array([212, 0, 0, 0, 8, 0, 39, 206, 48, 29, 207, 179, 183, 67])
print("msdu", type(msdu))
for x in msdu:
	bin_x = bin(x)
	print(x, bin_x)
	pass

# print('-----------')
# print(msdu[0]>>4)
# print(msdu[0]>>2 & 3)

frame_control = msdu[0]
frame_duration = msdu[1]
addr1 = msdu[4:10]
print(frame_control)
print(frame_duration)
print(addr1)