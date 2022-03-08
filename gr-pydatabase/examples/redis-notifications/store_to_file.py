from scipy.io import savemat
from time import sleep
import json
import redis as redis
import utils
import sys, os
import numpy as np
import os.path

r, _ = utils.redis_setup()

def get_ch(freq):
    if 2412e6 <= freq <= 2472e6:
        return int((freq-2412e6)/5e6 + 1)
    elif freq == 2484e6:
        return int(14)
    else:
        return int((freq-5170e6)/5e6 + 34)

def get_file_name(seq, fc, encoding, total):
    return f'csi_{seq}_{fc}_{encoding}_{total}.mat'


def get_csi_by_key(db_key):
    try:
        db_dict = r.hgetall(db_key)

        payload = json.loads(db_dict[b'payload'])

        info = json.loads(db_dict[b'info'])
        real_csi = np.array(info.pop('real'))
        imag_csi = np.array(info.pop('imag'))
        csi = real_csi + 1j*imag_csi
        info['csi'] = csi
        
        info['sequence'] = payload['sequence']
        info['rx_time'] = db_key.split(':')[2]
        info['tx_time'] = payload['timestamp']
        info['total'] = payload['total']
        info['idx'] = payload['idx']

        return info
    except:
        print(f'Cannot get db value from key: {db_key}')
    
def save_to_file(save_dir, file_name, save_dict):
    try:
        if os.path.isfile(f'{save_dir}{file_name}'):
            raise RuntimeError('File already exists. Abort')
        else:
            print(f'Save to {save_dir}{file_name}...')
            savemat(f'{save_dir}{file_name}', {'data':save_dict})

    except Exception as e:
        print(f'Cannot save to {save_dir}/{file_name}. {e}')
        pass

def main():
    if len(sys.argv) != 3:
        print('Input arguments should be exactly 2.')
        print('~$ python store_to_file.py {folder} {store_sequence_id}')
        print('Example: \n\t~$ python store_to_file.py \"./directory/to/store/folder\" \"tx\"')
        sys.exit()
        pass
    elif not os.path.isdir(sys.argv[1]):
        print(f'The target folder {sys.argv[1]} does not exist.')
        sys.exit()
    
    save_dir = sys.argv[1]
    seq_id = sys.argv[2]

    # Get all the keys in db and decodes keys as utf8 format
    keys = [utils.utf8_decode(key) for key in r.keys('*')]

    dict_array = []
    total_recv = 0
    for key in keys:
        info = json.loads(utils.utf8_decode(r.hget(key, 'payload')))
        if info['sequence'] == seq_id:
            total_recv = total_recv + 1
            db_dict = get_csi_by_key(key)
            dict_array.append(db_dict)
            if not 'ch' in locals():
                ch = get_ch(db_dict['nominal frequency'])
            if not 'encoding' in locals():
                encoding = db_dict['encoding']
            if not 'total' in locals():
                total = db_dict['total']
    
    file_name = get_file_name(seq_id, ch, encoding, total)
    print(f'Total receive {total_recv} packets.')
    save_to_file(save_dir, file_name, dict_array)
    
    
    

if __name__ == "__main__":
    main()
