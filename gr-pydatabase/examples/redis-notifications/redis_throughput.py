import redis as redis
import utils
import time

r, subprefix = utils.redis_setup(db_host='localhost', db_port=6379, db_ch='channel_1', db_idx=0)

def main():
	Loop_MAX = 10000
	start_time = time.time()
	

	for x in range(Loop_MAX):
		r.set("Test:"+str(x), x)
		pass

	print("Total time: ", time.time()-start_time)

if __name__ == '__main__':
	main()
