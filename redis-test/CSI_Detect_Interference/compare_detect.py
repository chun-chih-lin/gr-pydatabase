import numpy as np
from matplotlib import pyplot as plt
from scipy import signal

from os import system
import sys
system("cls")

def read_npy(filename):
	with open(filename, 'rb') as f:
		npy_data = np.load(f)
	return npy_data

# ===============================================================
def bandpass_filter(data, lowcutoff=.9, highcutoff=5):
	fs = 52
	nyq = fs/2.0
	nor_lowcutoff = lowcutoff / nyq
	nor_highcutoff = highcutoff / nyq
	order = 5
	b, a = signal.butter(order, [nor_lowcutoff, nor_highcutoff], btype='band', analog=False)
	y = signal.filtfilt(b, a, data)
	return y

def get_slope(ary, l):
	slope_ary = []
	for i, s in enumerate(ary[:l-1]):
		slope = ary[i+1]-ary[i]
		slope_ary.append(slope)
	return slope_ary

def detecting_interference(csi_ary, sig_type=None):
	def detect_csi_by_slope(csi):
		slope_threshold = 0.015
		sub_csi_1 = abs(csi[:-1])
		sub_csi_2 = abs(csi[1:])
		slope = sub_csi_2-sub_csi_1
		s_mean = np.mean(abs(slope))
		
		detect = [0 if abs(s) <= slope_threshold else 1 for s in slope]
		
		detected = 0
		if sum(detect) > 1:
			detected = 1
		return detected

	def detect_csi_by_filter(csi, threshold=0.03):
		# print(f'{list(abs(csi)) = }', end=', ')
		if any(s >= threshold for s in abs(csi)):
			# print(1)
			return 1
		# print(0)
		return 0

	# -----------------------
	def get_bandpass_csi(csi_ary, lowcutoff=.9, highcutoff=5):
		filtered_ary = []
		for csi in csi_ary:
			filtered = bandpass_filter(csi, lowcutoff=lowcutoff, highcutoff=highcutoff)
			filtered_ary.append(filtered)
		return filtered_ary

	sig_ary = []
	for csi in csi_ary:
		if abs(csi[0]) != 0:
			sig_ary.append(csi)
	sig_ary = csi_ary

	filtered = get_bandpass_csi(abs(sig_ary), lowcutoff=.9, highcutoff=18)

	# plt.figure()
	# plt.subplot(121)
	# for csi in filtered:
	# 	plt.plot(csi)
	# plt.ylim(-.12, .12)
	# plt.grid(True)

	# plt.subplot(122)
	# for csi in sig_ary:
	# 	plt.plot(abs(csi))
	# plt.grid(True)


	detection_slope = []
	detection_filter = []
	filter_threshold = 0.02
	for csi_i, csi in enumerate(sig_ary):
		detect_filter = detect_csi_by_filter(filtered[csi_i], filter_threshold)
		detect_slope = detect_csi_by_slope(csi)
		detection_filter.append(detect_filter)
		detection_slope.append(detect_slope)

	plt.figure()
	plt.subplot(121)
	for csi in filtered:
		plt.plot(csi, color='grey', linewidth=1, alpha=0.5)
	for csi, d in zip(filtered, detection_filter):
		if d == 0:
			plt.plot(csi, color='tab:blue', linewidth=.5)
	plt.ylim(-.12, .12)
	plt.axhline(filter_threshold, color='r', linewidth=.5)
	plt.grid(True)

	plt.subplot(122)
	for csi in filtered:
		plt.plot(csi, color='grey', linewidth=1, alpha=0.5)
	for csi, d in zip(filtered, detection_filter):
		if d == 1:
			plt.plot(csi, color='tab:red', linewidth=.5)
	plt.ylim(-.12, .12)
	plt.axhline(filter_threshold, color='r', linewidth=.5)
	plt.grid(True)

	plt.figure()
	plt.subplot(121)
	for csi in sig_ary:
		plt.plot(abs(csi), color='grey', linewidth=1, alpha=0.5)
	for csi_i, (csi, d_s, d_f) in enumerate(zip(sig_ary, detection_slope, detection_filter)):
		if d_s == d_f == 0:
			color = 'tab:blue'
			plt.plot(abs(csi), color=color, linewidth=.5)
	plt.ylim(0, 0.52)
	plt.xlim(0, 51)
	plt.grid(True)
	plt.title('Normal signal')

	plt.subplot(122)
	for csi in sig_ary:
		plt.plot(abs(csi), color='grey', linewidth=1, alpha=0.5)
	for csi_i, (csi, d_s, d_f) in enumerate(zip(sig_ary, detection_slope, detection_filter)):
		if d_s == d_f == 1:
			color = 'tab:red'
			plt.plot(abs(csi), color=color, linewidth=.5)
	plt.ylim(0, 0.52)
	plt.xlim(0, 51)
	plt.grid(True)
	plt.title('Interfered signal')

	if sig_type is not None:
		plt.suptitle(sig_type)

	return detection_slope
	

def process(csi_ary, timestamp_ary, sig_type='None'):
	# detecting for the interference
	detected = detecting_interference(csi_ary, sig_type=sig_type)

	if detected is None:
		return

	time_ary = [timestamp_ary[np.nonzero(timestamp_ary)[0][0]]]
	for t_i, time in enumerate(timestamp_ary):
		if time == 0:
			time_ary.append(time_ary[t_i-1])
		else:
			time_ary.append(time)
	
	# plt.figure()
	# for i, (d, t) in enumerate(zip(detected, timestamp_ary)):
	# 	if t != 0:
	# 		color = "tab:blue"
	# 		if d == 1:
	# 			color = "tab:red"
	# 		plt.plot(i, t, color=color, marker='.')
	# plt.grid(True)

	
# ===============================================================
def main():
	n_csi = read_npy('ch_13_no_inter_csi.npy')
	n_timestamp = read_npy('ch_13_no_inter_timestamp.npy')
	w_csi = read_npy('ch_13_wi_inter_csi.npy')
	w_timestamp = read_npy('ch_13_wi_inter_timestamp.npy')

	process(n_csi, n_timestamp, sig_type='No Inter')
	process(w_csi, w_timestamp, sig_type='With Inter')
	plt.show()
	pass

if __name__ == '__main__':
	main()
