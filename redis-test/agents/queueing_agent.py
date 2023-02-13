import numpy as np
import redis as redis
import utils
import time
import json
import random
import string

class QueueAgent(object):
    """docstring for QueueAgent"""
    def __init__(self, subprefix, agentkey):
        super(QueueAgent, self).__init__()
        print('Initialing QueueAgent...')
        self.db_host = 'localhost'
        self.db_port = 6379
        self.db_idx = 0
        self.subprefix = subprefix
        self.agentkey = agentkey

        self.db = redis.Redis(host=self.db_host, port=self.db_port, db=self.db_idx)
        self.subpattern = f'__keyspace@{self.db_idx}__:{self.subprefix}'
        self.agentpattern = f'__keyspace@{self.db_idx}__:{self.agentkey}'

        self.check_notify()

        self.pubsub = self.db.pubsub()
        self.pubsub.psubscribe(**{self.subpattern: self.event_handler})
        self.pubsub.psubscribe(**{self.agentpattern: self.agent_event_handler})
        self.thread = self.pubsub.run_in_thread(sleep_time=0.001)

        self.RETRY_MAX = 5
        self.WAIT_MAX = 0.001
        self.RFDEVICE_STATE = "RFDEVICE:STATE"

        self.KEYWORD_QUIT = "Quit"
        self.KEYWORD_BUSY = "Busy"
        self.KEYWORD_IDLE = "Idle"
        self.KEYWORD_STOP = "Stop"
        self.KEYWORD_WAIT_ACK = "WAITACK"
        self.KEYWORD_TRANS = "TRANSMISSION"

        self.SYSTEM_STATE = "RFSYSTEM:STATE"
        self.SYSTME_FREE = "Free"
        self.SYSTEM_TRANS_HOLD = "Hold"
        print('Initialization done.')

    def check_notify(self):
        self.db.config_set('notify-keyspace-events', 'KEA')

    def utf8_decode(self, msg):
        return msg.decode("utf-8")

    def agent_event_handler(self, msg):
        try:
            key = self.utf8_decode(msg["channel"])
            if key:
                db_key = self.utf8_decode(self.db.get(self.agentkey))
                if db_key == self.KEYWORD_QUIT:
                    print('Quiting QueueAgent. See you again.')
                    self.db.set('AGENT:QUEUE', self.KEYWORD_STOP)
                    self.thread.stop()
        except Exception as exp:
            print(f'[Queue] Exception occurs: {exp}')

    def event_handler(self, msg):
        try:
            key = self.utf8_decode(msg["channel"])
            if key:
                # get the db_key for transmission information
                db_key = "QUEUE:LIST:TRANS"
                self.process_message(db_key)
        except Exception as exp:
            print(f'[Queue] Exception occurs: {exp}')

    def process_message(self, db_key):
        while self.db.exists(db_key):
            # While "QUEUE:LIST:TRANS" exist, means there is message needs to be transmitted
            print(f'[Queue] {self.db.get(self.RFDEVICE_STATE)}')
            rf_device_state = self.utf8_decode(self.db.get(self.RFDEVICE_STATE))
                        
            if rf_device_state == self.KEYWORD_IDLE:
                # There are some keys in the queue and the RF is Idle.
                oldest_key = self.utf8_decode(self.db.lrange(db_key, -1, -1)[0])
                # Trigger the Transmission Agent to transmit
                # Set the state of RF as Busy
                p = self.db.pipeline()
                # Tell the transmission agent which key to be transmitted
                # print(f'Tell transmission agent to trans {oldest_key}')
                p.set(self.KEYWORD_TRANS, oldest_key)
                # Set rf device to Busy
                p.set(self.RFDEVICE_STATE, self.KEYWORD_BUSY)
                p.execute()
            elif self.db.get(self.SYSTEM_STATE).decode('utf-8') == self.SYSTEM_TRANS_HOLD:
                return
            else:
                print('[Queue] Still processing, sleep for 0.001 second.')
                time.sleep(0.001)
            print('Done processing all the msg in queue')

def main():
    QueueAgent('QUEUE:LIST:TRANS', 'AGENT:QUEUE')

if __name__ == '__main__':
    main()
