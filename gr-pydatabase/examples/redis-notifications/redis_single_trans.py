import numpy as np
import redis as redis
import utils
import time
import json
import random
import string
from time import sleep
from datetime import datetime
import sys
import argparse

Loop_MAX = 1000
# The maximum MSDU is 1500 bytes before encryption.
MSDU_MAX = 200

# print(f'len input: {len(sys.argv)}')

input_c = len(sys.argv)

"""
ID = "a"
sleep_bw_pkt = 0.001
Message = None

if input_c >= 2:
    ID = sys.argv[1]
if input_c >= 3:
    Message = sys.argv[2]
if input_c >= 4:
    sleep_bw_pkt = float(sys.argv[3])
if input_c >= 5:
    Loop_MAX=int(sys.argv[4])
"""

r, subprefix = utils.redis_setup(db_host='localhost', db_port=6379, db_ch='channel_1', db_idx=0)

def parse_arg():
    DEFAULT_N_PKT = 10
    DEFAULT_INTERVAL = 0.001

    parser = argparse.ArgumentParser(description="This script is the interface between user and the RF front-end.")
    parser.add_argument("--id", type=str, default="ID",
                        help="The id of transmitted packets.")
    parser.add_argument("--msg", type=str,
                        help="The transmitted message.")
    parser.add_argument("--itvl", type=float, default=DEFAULT_INTERVAL,
                        help="The interval between two packets can be sent out.")
    parser.add_argument("--n_pkt", type=int, default=DEFAULT_N_PKT,
                        help="The number of transmitted packets.")
    args = parser.parse_args()
    return args.id, args.msg, args.itvl, args.n_pkt

def generate_MSDU(idx, seq_id, Message, sleep_bw_pkt, Loop_MAX):
    print(f'Generating [{idx+1}/{Loop_MAX}] packet...', end='\r')
    MSDU = dict()
    MSDU["idx"] = str(idx)
    MSDU["total"] = str(Loop_MAX)
    MSDU["sequence"] = seq_id + '.' + str(time.time())
    MSDU["data"] = ""
    MSDU["timestamp"] = str(time.time())
    length_remain = len(json.dumps(MSDU))
    if Message is None:
        MSDU["data"] = "".join(random.choice(string.ascii_letters) for x in range(MSDU_MAX - length_remain))
    else:
        MSDU["data"] = Message
    # print(f"MSDU_MAX - length_remain = {MSDU_MAX} - {length_remain} = {MSDU_MAX - length_remain}")
    print(f"\nSending data: {MSDU['data']}.....")
    return json.dumps(MSDU, separators=(',', ':'))

def run_without_pipeline(seq_id, Message, sleep_bw_pkt, Loop_MAX):
    start_time = time.time()
    for x in range(Loop_MAX):
        set_value = generate_MSDU(x, seq_id, Message, sleep_bw_pkt, Loop_MAX)
        action_key = "Single:Trans:"+str(x)
        r.delete(action_key)
        r.set(action_key, set_value)
        r.lpush("QUEUE:LIST:TRANS", action_key)
        sleep(sleep_bw_pkt)
        pass

    print("Total time w/o pipeline: ", time.time()-start_time)
    print("list: ", r.lrange("QUEUE:LIST:TRANS", 0, -1))
    pass

def run_with_pipeline(seq_id, Message, sleep_bw_pkt, Loop_MAX):
    start_time = time.time()
    p = r.pipeline()
    for x in range(Loop_MAX):
        set_value = generate_MSDU(x, seq_id, Message, sleep_bw_pkt, Loop_MAX)
        r.delete("Single:trans")
        r.set("Single:trans", set_value)
        r.lpush("QUEUE:LIST:TRANS", "Single:trans")
    p.execute()
    print("Total time w/ pipeline: ", time.time()-start_time)
    print("list: ", r.smembers("QUEUE:LIST:TRANS"))

def main():
    seq_id, Message, sleep_bw_pkt, Loop_MAX = parse_arg()

    print("Start transmitting packets...")
    print(f"Rest interval: {sleep_bw_pkt} seconds.")
    print(f"Sequence: {seq_id}, Total packets: {Loop_MAX}")
    run_without_pipeline(seq_id, Message, sleep_bw_pkt, Loop_MAX)
    # run_with_pipeline(seq_id, Message, sleep_bw_pkt, Loop_MAX)

if __name__ == '__main__':
    main()
