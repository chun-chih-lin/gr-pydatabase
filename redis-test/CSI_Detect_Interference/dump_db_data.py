import redis
import json
import numpy as np
import matplotlib.pyplot as plt

db = redis.Redis(host='localhost', port=6379, db=0)

def save_numpy(filename, np_ary):
    with open(filename, 'wb') as f:
        np.save(f, np_ary)


def detecting(k, filename):
    key = f'Recv:{k}*'

    print(f'keys: {key}')
    db_keys = db.keys(key)
    
    print(f'total keys: {len(db_keys)}')

    ttl_snr = np.zeros(1000)
    ttl_csi = np.zeros((1000, 52), dtype=np.complex)
    print(ttl_csi.shape)
    ttl_timestamp = np.zeros(1000)
    print(ttl_snr.shape)

    for k_i, db_key in enumerate(db_keys):
        data_info = db.hget(db_key, 'info').decode('utf-8')
        data_payload = db.hget(db_key, 'payload').decode('utf-8')

        json_info = json.loads(data_info)
        json_payload = json.loads(data_payload)
        
        snr = json_info['snr']
        csi = [r+1j*i for r, i in zip(json_info['real'], json_info['imag'])]
        idx = int(json_payload['idx'])
        total = json_payload['total']
        timestamp = float(json_payload['timestamp'])

        ttl_snr[idx] = snr
        ttl_csi[idx][:] = csi
        ttl_timestamp[idx] = timestamp
    
    #save_numpy(f'{filename}_snr.np', ttl_snr)
    #save_numpy(f'{filename}_csi.np', ttl_csi)
    #save_numpy(f'{filename}_timestamp.np', ttl_timestamp)

def main():
    keys = ['2465_n10', '2465_n20', '2470_n10', '2470_n20']
    files = ['2465_n20', '2465_n10', '2470_n10', '2470_n20']
    for key, filename in zip(keys, files):
        print(f'Processing for key: {key}')
        detecting(key, filename)
    print('Done')

if __name__ == "__main__":
    main()
