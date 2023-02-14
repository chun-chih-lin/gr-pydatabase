import redis as redis
import time
import json

from operator import attrgetter
from collections import namedtuple

ReceivedMsg = namedtuple('ReceivedMsg', ['id', 'total', 'seq', 'timestamp', 'data'])

db = redis.Redis(host='localhost', port=6379, db=0)

def evaluation(db_keys):
    received_list = []
    for _, key in enumerate(db_keys):
        hash_value = db.hgetall(key)
        try:
            payload = json.loads(hash_value[b'payload'])

            seq = payload['sequence'].split('.')[0]

            received = ReceivedMsg(int(payload['idx']), int(payload['total']), 
                                   seq, float(payload['timestamp']), payload['data'])
            received_list.append(received)
        except Exception as e:
            print(f'Exception: {e}')

    sorted_msg = sorted(received_list, key=attrgetter('timestamp'))
    return sorted_msg

def display_results(msgs):
    show_data_len = 30

    str_id, str_ttl, str_seq, str_time, str_data = "ID", "Total", "Sequence", "TimeStamp", "Message"
    print("==============================================================")
    print(f'{str_id:>3}/{str_ttl:<10} {str_seq:<10} {str_data:<34}')
    print("--------------------------------------------------------------")
    recv_pkt = 0
    last_idx = 0
    for message in msgs:
        idx, ttl, seq, timestamp, data = message
        print(f'{idx+1:>3}/{ttl:<10} {seq:<10} {data[0:show_data_len]}', end='')
		
        if idx < last_idx:
            print(f"\n--- Reception Rate: {recv_pkt/ttl*100:.2f}")
            recv_pkt = 0
        else:
            recv_pkt += 1

        if len(data) > show_data_len:
            print('...', end='')
        print('')
        last_idx = idx
    try:
        print(f"--- Reception Rate: {recv_pkt/ttl*100:.2f}")
    except Exception as exp:
        pass
    pass

def main():
    all_keys = db.keys('Recv:*')
    stored_msg = evaluation(all_keys)
    display_results(stored_msg)
    pass

if __name__ == '__main__':
	main()
