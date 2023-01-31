import numpy as np
from matplotlib import pyplot as plt
from scipy import signal

import sys

def read_npy(prefix):
	with open(f'{prefix}_csi.npy', 'rb') as f:
		csi = np.load(f)
	with open(f'{prefix}_snr.npy', 'rb') as f:
		snr = np.load(f)
	with open(f'{prefix}_timestamp.npy', 'rb') as f:
		timestamp = np.load(f)
	return snr, csi, timestamp

def buter_highpass_filter(data, cutoff, fs, order=5):
	nyq = 0.5 * fs
	normal_cutoff = cutoff / nyq
	b, a = signal.butter(order, normal_cutoff, btype='high', analog=False)
	filtered = signal.filtfilt(b, a, data)
	return filtered

def fft_test():
	if True:
		return
	fs = 10
	t = np.arange(0, 52, 1/fs)
	sig_f = 4
	sp = np.fft.fft(np.sin(2*np.pi*sig_f*t))
	freq = np.fft.fftfreq(t.shape[-1])*fs 

	plt.figure()
	plt.plot(freq, sp.real)
	plt.plot(freq, sp.imag)
	plt.plot(freq, abs(sp))

def detecting_interference(csi_ary):
	csi_l = 52
	linspace = [i for i in range(csi_l)]
	avg_len = 2

	slope_threshold_min = 0.80
	slope_threshold_max = 1.2
	detection = np.zeros(len(csi_ary))
	received_packets = 0

	plt.figure()
	plt.subplot(221)
	fft_detect = []
	for csi_i, csi in enumerate(csi_ary):
		fft_csi = np.fft.fft(csi)
		plt.plot(fft_csi.real)
		plt.plot(fft_csi.imag)
		if any(abs(fft_csi) > 1):
			fft_detect.append(1)
		else:
			fft_detect.append(0)
	# plt.ylim(0, 15)
	plt.grid(True)

	plt.subplot(222)
	for csi_i, (csi, detect) in enumerate(zip(csi_ary, fft_detect)):
		fft_csi = np.fft.fft(csi)
		color = 'red'
		if detect == 0:
			color = 'blue'
		plt.plot(fft_csi.real, color=color)
		plt.plot(fft_csi.imag, color=color)
	plt.grid(True)

	plt.subplot(223)
	for csi_i, csi in enumerate(csi_ary):
		if fft_detect[csi_i] == 1:
			color = 'red'
			plt.plot(np.abs(csi), color=color)
		else:
			color = 'blue'
	plt.grid(True)
	plt.ylim(0, 0.6)
	plt.xlabel('sample')
	plt.ylabel('csi')

	plt.subplot(224)
	for csi_i, csi in enumerate(csi_ary):
		if fft_detect[csi_i] == 1:
			color = 'red'
		else:
			color = 'blue'
			plt.plot(np.abs(csi), color=color)
	plt.grid(True)
	plt.ylim(0, 0.6)
	plt.xlabel('sample')
	plt.ylabel('csi')

	# plt.figure()
	# plt.subplot(311)
	# for csi_i, csi in enumerate(csi_ary):
	# 	cutoff = 2
	# 	fs = 52
	# 	order = 5
	# 	filtered = buter_highpass_filter(csi, cutoff, fs, order=order)
	# 	plt.plot(filtered)
	# plt.grid(True)

	# plt.subplot(312)
	# plt.axhline(y = slope_threshold_min, color='red', linestyle='dotted')
	# plt.axhline(y = slope_threshold_max, color='red', linestyle='dotted')
	# for csi_i, csi in enumerate(csi_ary):
	# 	slopes = []
	# 	if csi[0] != 0:
	# 		received_packets += 1
	# 	for i, s in enumerate(csi):
	# 		if i < csi_l - avg_len:
	# 			if abs(csi[i+avg_len]) == 0:
	# 				slope = 0
	# 				break
	# 			else:
	# 				slope = abs(csi[i]) / abs(csi[i+avg_len])
	# 			slopes.append(slope)
	# 			if slope_threshold_min > slope or slope > slope_threshold_max and detection[csi_i] == 0:
	# 				detection[csi_i] = 1
	# 	plt.plot(slopes)
	# plt.grid(True)
	
	print(f'Total received packets: {received_packets}')
	print(f'Interfered packets: {sum(fft_detect)}')

	# plt.subplot(313)
	# for csi_i, csi in enumerate(csi_ary):
	# 	if detection[csi_i] == 1:
	# 		color = 'red'
	# 	else:
	# 		color = 'blue'
	# 	plt.plot(np.abs(csi), color=color)
	# plt.grid(True)
	# plt.xlabel('sample')
	# plt.ylabel('csi')

	fft_test()

	plt.show()

	


def process(prefix):
	snr, csi, timestamp = read_npy(prefix)

	detecting_interference(csi)

def main():
	try:
		filename = sys.argv[1]
	except Exception as exp:
		print(exp)
		return
	process(filename)


if __name__ == "__main__":
	main()
