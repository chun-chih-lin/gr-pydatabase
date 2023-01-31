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
		if any(s >= threshold for s in abs(csi)):
			return 1
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

	def get_energy(signal):
		return np.square(signal)

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
	detection_energy = []
	plt.subplot(131)
	for csi in filtered:
		if abs(csi)[0] != 0:
			energy_csi = get_energy(csi)
			t3 = np.quantile(energy_csi, 0.9)
			coefficient = 2.5
			detect = np.nonzero(energy_csi > coefficient*t3)[0]
			
			if len(detect) >= 3:
				detection_energy.append(1)
				color = 'tab:red'
			elif any(e > 0.0009 for e in energy_csi):
				detection_energy.append(1)
				color = 'tab:red'
			else:
				detection_energy.append(0)
				color = 'tab:blue'
				plt.plot(energy_csi, color=color)
			# plt.axhline(t3, color='red', linewidth=.5)
		else:
			detection_energy.append(0)
	plt.grid(True)
	plt.ylim(0, 0.01)

	plt.subplot(221)
	for csi in filtered:
		energy_csi = get_energy(csi)
		plt.plot(abs(energy_csi), color='grey', linewidth=.5, alpha=.5)
	for (csi, d) in zip(filtered, detection_energy):
		energy_csi = get_energy(csi)
		if d == 0:
			color = 'tab:blue'
			plt.plot(abs(energy_csi), color=color, linewidth=.5)
	plt.axhline(0.0009, color='red', linewidth=.5)
	plt.grid(True)

	plt.subplot(222)
	for csi in filtered:
		energy_csi = get_energy(csi)
		plt.plot(abs(energy_csi), color='grey', linewidth=.5, alpha=.5)
	for (csi, d) in zip(filtered, detection_energy):
		energy_csi = get_energy(csi)
		if d == 1:
			color = 'tab:red'
			plt.plot(abs(energy_csi), color=color, linewidth=.5)
	plt.axhline(0.0009, color='red', linewidth=.5)
	plt.grid(True)

	plt.subplot(223)
	for csi in sig_ary:
		plt.plot(abs(csi), color='grey', linewidth=.5, alpha=.5)
	for (csi, d) in zip(sig_ary, detection_energy):
		if d == 0:
			color = 'tab:blue'
			plt.plot(abs(csi), color=color, linewidth=.5)
	plt.grid(True)

	plt.subplot(224)
	for csi in sig_ary:
		plt.plot(abs(csi), color='grey', linewidth=.5, alpha=.5)
	for (csi, d) in zip(sig_ary, detection_energy):
		if d == 1:
			color = 'tab:red'
			plt.plot(abs(csi), color=color, linewidth=.5)
	plt.grid(True)




	


	"""
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
	"""

	"""
	plt.figure(figsize=(14, 6), dpi=80)
	plt.subplot(221)
	for csi in sig_ary:
		plt.plot(abs(csi), color='grey', linewidth=1, alpha=0.5)
	for csi_i, (csi, d_s, d_f) in enumerate(zip(sig_ary, detection_slope, detection_filter)):
		if d_f == 0:
			color = 'tab:blue'
			plt.plot(abs(csi), color=color, linewidth=.5)
	plt.ylim(0, 0.52)
	plt.xlim(0, 51)
	plt.grid(True)
	plt.title('(filtered) Normal signal')

	plt.subplot(222)
	for csi in sig_ary:
		plt.plot(abs(csi), color='grey', linewidth=1, alpha=0.5)
	for csi_i, (csi, d_s, d_f) in enumerate(zip(sig_ary, detection_slope, detection_filter)):
		if d_s == 0:
			color = 'tab:blue'
			plt.plot(abs(csi), color=color, linewidth=.5)
	plt.ylim(0, 0.52)
	plt.xlim(0, 51)
	plt.grid(True)
	plt.title('(Slope) Normal signal')

	plt.subplot(223)
	for csi in sig_ary:
		plt.plot(abs(csi), color='grey', linewidth=1, alpha=0.5)
	for csi_i, (csi, d_s, d_f) in enumerate(zip(sig_ary, detection_slope, detection_filter)):
		if d_f == 1:
			color = 'tab:red'
			plt.plot(abs(csi), color=color, linewidth=.5)
	plt.ylim(0, 0.52)
	plt.xlim(0, 51)
	plt.grid(True)
	plt.title('(filtered) Interfered signal')

	plt.subplot(224)
	for csi in sig_ary:
		plt.plot(abs(csi), color='grey', linewidth=1, alpha=0.5)
	for csi_i, (csi, d_s, d_f) in enumerate(zip(sig_ary, detection_slope, detection_filter)):
		if d_s == 1:
			color = 'tab:red'
			plt.plot(abs(csi), color=color, linewidth=.5)
	plt.ylim(0, 0.52)
	plt.xlim(0, 51)
	plt.grid(True)
	plt.title('(Slope) Interfered signal')
	"""

	if sig_type is not None:
		plt.suptitle(sig_type)
	return detection_slope


# ===============================================================
def preprecessing(csi_ary):

	pass

# ===============================================================
def process(csi_ary, timestamp_ary, sig_type='None'):
	# preprecessing(csi_ary)
	# if True:
	# 	return
	# detecting for the interference
	detected = detecting_interference(csi_ary, sig_type=sig_type)

	if detected is None:
		return None
	return detected

	
# ===============================================================
def main():
	n_csi = read_npy('ch_13_no_inter_csi.npy')
	n_timestamp = read_npy('ch_13_no_inter_timestamp.npy')
	w_csi = read_npy('ch_13_wi_inter_csi.npy')
	w_timestamp = read_npy('ch_13_wi_inter_timestamp.npy')

	detected_no_inter = process(n_csi, n_timestamp, sig_type='No Inter')
	detected_wi_inter = process(w_csi, w_timestamp, sig_type='With Inter')
	
	plt.show()
	pass

if __name__ == '__main__':
	main()
