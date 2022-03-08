import socket

MESSAGE = "Hello, from python, UDP!\n"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(MESSAGE.encode(), ("127.0.0.1", 52001))
