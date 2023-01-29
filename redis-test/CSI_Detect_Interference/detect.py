import numpy as np
import matplotlib.pyplot as plt
import sys

def read_np(prefix):
	with open(f'{prefix}_csi.np', 'rb') as f:
		csi = np.load(f)
	with open(f'{prefix}_snr.np', 'rb') as f:
		snr = np.load(f)
	with open(f'{prefix}_timestamp.np', 'rb') as f:
		timestamp = np.load(f)
	return snr, csi, timestamp

def show_graph(snr, csi, timestamp, title_name):
	plt.figure()
	plt.plot(snr)
	plt.grid(True)
	plt.title(title_name)
	plt.show()

def detect(prefix):
	print(f'{prefix}_snr.np')
	snr, csi, timestamp = read_np(prefix)
	show_graph(snr, csi, timestamp, prefix)
	
	

def main():
	print('test')
	try:
		filename = sys.argv[1]
	except Exception as exp:
		print(exp)
		return
	detect(filename)


if __name__ == "__main__":
	main()
