import numpy as np
from matplotlib import pyplot as plt

import sys

def read_np(prefix):
	with open(f'{prefix}_csi.npy', 'rb') as f:
		csi = np.load(f)
	with open(f'{prefix}_snr.npy', 'rb') as f:
		snr = np.load(f)
	with open(f'{prefix}_timestamp.npy', 'rb') as f:
		timestamp = np.load(f)
	return snr, csi, timestamp

def show_graph(snr, csi, times, title_name):

	print(f'received packets: {len(np.nonzero(snr)[0])}')

	plt.figure()

	# pre_time_idx = np.nonzero(times)[0][0]
	# times = times - times[pre_time_idx]
	# calibrate_time = []
	# for i, t in enumerate(times):
	# 	if t < 0:
	# 		calibrate_time.append(calibrate_time[i-1])
	# 	else:
	# 		calibrate_time.append(t)
	# plt.plot(calibrate_time)
	# plt.grid(True)

	for pkt in csi:
		plt.plot(pkt.real, color='blue')
		plt.plot(pkt.imag, color='red')
		plt.plot(np.abs(pkt), color='green')
	plt.grid(True)
	plt.title(title_name)
	plt.xlabel('sample')
	plt.ylabel('csi')

	# plt.show()

def detecting_interference(csi_ary):
	csi_l = 52
	avg_len = 2

	plt.figure()
	slope_threshold_min = 0.80
	slope_threshold_max = 1.2
	detection = np.zeros(len(csi_ary))
	received_packets = 0
	for csi_i, csi in enumerate(csi_ary):
		slopes = []
		if csi[0] != 0:
			received_packets += 1
		for i, s in enumerate(csi):
			if i < csi_l - avg_len:
				if abs(csi[i+avg_len]) == 0:
					slope = 0
					break
				else:
					slope = abs(csi[i]) / abs(csi[i+avg_len])
				slopes.append(slope)
				if slope_threshold_min > slope or slope > slope_threshold_max and detection[csi_i] == 0:
					detection[csi_i] = 1
		plt.plot(slopes)
	plt.grid(True)
	
	print(f'Total received packets: {received_packets}')
	print(f'Interfered packets: {sum(detection)}')

	plt.figure()
	for csi_i, csi in enumerate(csi_ary):
		if detection[csi_i] == 1:
			color = 'red'
		else:
			color = 'blue'
		plt.plot(np.abs(csi), color=color)
	plt.grid(True)
	plt.xlabel('sample')
	plt.ylabel('csi')

	plt.show()

	


def process(prefix):
	snr, csi, timestamp = read_np(prefix)

	detecting_interference(csi)

	if True:
		return
	show_graph(snr, csi, timestamp, prefix)

def main():
	try:
		filename = sys.argv[1]
	except Exception as exp:
		print(exp)
		return
	process(filename)


if __name__ == "__main__":
	main()
