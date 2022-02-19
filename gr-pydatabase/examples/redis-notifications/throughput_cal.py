import numpy as np
import json
import utils
import time
import array

r, subprefix = utils.redis_setup(db_host='localhost', db_port=6379, db_ch='channel_1', db_idx=0)

def main():
	redis_keys = r.keys("*")
	
	min_time = time.time()
	max_time = 0.0
	time_stamp_float = list()
	# total_list = [idx for idx in range(1000)]
	Total_duration = 0.0
	Trans_size = 0
	for key in redis_keys:
		time_stamp = float(key.decode("utf-8").split(":")[1])
		time_stamp_float.append(time_stamp)
		value = r.get(key.decode("utf-8"))
		value_dict = json.loads(value)
		# total_list.remove(int(value_dict["idx"]))

		received_time = float(key.decode("utf-8").split(":")[1])
		transmit_time = float(value_dict["timestamp"])
		duration_time = received_time - transmit_time
		Total_duration += duration_time

		Trans_size += len(value)


	print("Total Duration: ", Total_duration)
	print("Total Transmitted: ", Trans_size)
	print("Throughput: ", Trans_size*8/Total_duration/1000/1000, " Mbps")
	# Time_duration = max(time_stamp_float)-min(time_stamp_float)
	# print(min(time_stamp_float), " ", max(time_stamp_float))
	# print("Time duration: ", max(time_stamp_float)-min(time_stamp_float)) 
	# print("Total Packets: ", len(time_stamp_float))
	# print(len(time_stamp_float)*8*1000/Time_duration/1000/1000, " Mbps.")
	# print("Total Lost: ", total_list)
	r.flushall()

if __name__ == '__main__':
	main()

