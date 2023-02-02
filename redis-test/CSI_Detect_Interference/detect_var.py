import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from os import system

"""
See Result.txt for the performance result.
"""

system('cls')

def read_npy(filename):
	with open(filename, 'rb') as f:
		npy_data = np.load(f)
	return npy_data

# =====================================================================
def get_recv_csi(csis, non_z_idx):
	recv_csi = []
	for csi, non_z in zip(csis, non_z_idx):
		if non_z == 1:
			recv_csi.append(csi)
	recv_csi = np.array(recv_csi)
	return recv_csi

def sliding_var_detect(csis, sliding_window_size=3):
	sliding_detect_csis = np.zeros((csis.shape[0], csis.shape[1]-sliding_window_size))
	for csi_i, csi in enumerate(csis):
		ret = []
		for i, s in enumerate(csi[:len(csi)-sliding_window_size]):
			ret.append(np.mean(np.var(csi[i:i+sliding_window_size])))

		sliding_detect_csis[csi_i, :] = ret
	return sliding_detect_csis

def median_max_detect(sliding_var_ary, median_threshold=4.5):
	median_max_detection = []
	for d_i, d in enumerate(sliding_var_ary):
		median = np.median(d)
		max_v = np.max(d)
		if median == 0:
			median_max_detection.append(0)
		elif max_v/median > median_threshold:
			median_max_detection.append(1)
		else:
			median_max_detection.append(0)
	return median_max_detection

def consecutive_detect(detections, non_z_idx):
	consecutive_detection = [a*b for (a, b) in zip(detections[:-1], detections[2:])]
	return consecutive_detection

def detecting(csis, times, non_z_idx, ttl_pkt, sliding_window_size=3, median_threshold=4.5, plot_flag=False):

	recv_csi = get_recv_csi(csis, non_z_idx)

	sliding_var_detect_csis = sliding_var_detect(recv_csi, sliding_window_size=sliding_window_size)
	detections = median_max_detect(sliding_var_detect_csis, median_threshold=median_threshold)
	consecutive_detection = consecutive_detect(detections, non_z_idx)

	if plot_flag:
		plt.figure()
		plt.subplot(221)
		for (csi, d) in zip(recv_csi, detections):
			color = 'tab:blue'
			if d == 1:
				color = 'tab:red'
			plt.plot(abs(csi), color=color)
		plt.grid(True)

		plt.subplot(222)
		for t_i, (t, d) in enumerate(zip(times, detections)):
			color = 'tab:blue'
			if d == 1:
				color = 'tab:red'
			plt.plot(t_i, d, color=color, marker='.')
		plt.grid(True)

		plt.subplot(223)
		for (csi, d) in zip(recv_csi, consecutive_detection):
			color = 'tab:blue'
			if d == 1:
				color = 'tab:red'
			plt.plot(abs(csi), color=color)
		plt.grid(True)

		plt.subplot(224)
		for t_i, (t, d) in enumerate(zip(times, consecutive_detection)):
			color = 'tab:blue'
			if d == 1:
				color = 'tab:red'
			plt.plot(t_i, d, color=color, marker='.')
		plt.grid(True)

	interfered = sum(consecutive_detection)
	noninterfered = ttl_pkt - sum(consecutive_detection)
	return interfered, noninterfered

# =====================================================================
def main():
	sliding_window_size = 3
	median_threshold = 4.25

	plot_flag = False

	n_csi = read_npy('ch_13_no_inter_csi.npy')
	n_timestamp = read_npy('ch_13_no_inter_timestamp.npy')
	n_non_zero = [1 if abs(c[0]) != 0 else 0 for c in n_csi]
	ttl_n_pkt = sum(n_non_zero)

	w_csi = read_npy('ch_13_wi_inter_csi.npy')
	w_timestamp = read_npy('ch_13_wi_inter_timestamp.npy')
	w_non_zero = [1 if abs(c[0]) != 0 else 0 for c in w_csi]
	ttl_w_pkt = sum(w_non_zero)

	sliding_window_size_ary = [3, 4, 5, 6]
	for sliding_window_size in sliding_window_size_ary:
		print(f'Sliding Window Size: {sliding_window_size}')
		median_threshold_ary = [th for th in np.arange(1.0, 5.25, 0.25, dtype=float)]
		no_inter_d_no = []
		no_inter_d_wi = []
		wi_inter_d_no = []
		wi_inter_d_wi = []
		for median_threshold in median_threshold_ary:

			num_inter, num_noninter = detecting(n_csi, n_timestamp, n_non_zero, ttl_n_pkt, \
					  sliding_window_size=sliding_window_size, median_threshold=median_threshold, plot_flag=plot_flag)
			no_inter_d_no.append(num_noninter)
			no_inter_d_wi.append(num_inter)

			num_inter, num_noninter = detecting(w_csi, w_timestamp, w_non_zero, ttl_w_pkt, \
					  sliding_window_size=sliding_window_size, median_threshold=median_threshold, plot_flag=plot_flag)
			wi_inter_d_no.append(num_noninter)
			wi_inter_d_wi.append(num_inter)

			if plot_flag:
				plt.show()

		for i, (th, no_no, no_wi, wi_no, wi_wi) in enumerate(zip(median_threshold_ary, \
										no_inter_d_no, no_inter_d_wi, wi_inter_d_no, wi_inter_d_wi)):
			no_accuracy = no_no/ttl_n_pkt*100
			wi_accuracy = wi_wi/ttl_w_pkt*100
			no_w = 1.0
			wi_w = 1.0/no_w
			avg_accuracy = (no_w*no_accuracy+wi_w*wi_accuracy)/2

			print(f'[{th:.3f}]  ({avg_accuracy:.2f})% Noninterfered: {no_no}/{no_wi} ({no_accuracy:.2f}%)  |  Interfered: {wi_no}/{wi_wi} ({wi_accuracy:.2f}%)')
	pass

if __name__ == '__main__':
	main()
