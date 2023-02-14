import numpy as np
import redis as redis
import utils
import time
import json
import random
import string

from BasicAgent import BasicAgent

class TransAgent(BasicAgent):
    def __init__(self, subprefix, agentkey):
        super(TransAgent, self).__init__("TransAgent", subprefix, agentkey)
        print('Initialization done.')

    def check_rf_state(self, state):
        if self.utf8_decode(self.db.get(self.c['REDEVICE_STATE'])) == state:
            pass
        else:
            self.db.set(self.c['REDEVICE_STATE'], state)

    def agent_event_handler(self, msg):
        try:
            key = self.utf8_decode(msg["channel"])
            if key:
                db_key = self.utf8_decode(self.db.get(self.agentkey))
                if db_key == self.c['KEYWORD_QUIT']:
                    print('Quiting TransAgent. See you again.')
                    self.db.set('AGENT:TRANS', self.c['KEYWORD_STOP'])
                    self.thread.stop()
        except Exception as exp:
            print(f'[Trans] Exception occurs: {exp}')
            pass

    def event_handler(self, msg):
        try:
            print(f'[Trans] Event! {msg}')
            # key should be 'TRANSMISSION'
            key = self.utf8_decode(msg["channel"])
            if key:
                # get the db_key for transmission information
                db_key = self.utf8_decode(self.db.get(self.subprefix))
                self.process_message(db_key)
        except Exception as exp:
            print(f'[Trans] Exception occurs: {exp}')

    def process_message(self, db_key):
        self.check_rf_state(state=self.c['KEYWORD_BUSY'])
        PMDU_msg = self.utf8_decode(self.db.get(db_key))

        # Trigger RF front-end to transmit the data
        # Add the key into waiting ACK list.
        p = self.db.pipeline()
        # Trigger the RF front-end to transmit
        print(f'=================== Transmitting Trans:{db_key}...')
        p.set(f'Trans:{db_key}', PMDU_msg)
        p.set(self.c['MONITOR_ACK'], self.c['ACK_STATE_WAIT'])
        p.execute()

        # Monitor the key and retransmit if needed
        self.monitor_key(db_key=db_key, PMDU_msg=PMDU_msg)

    def monitor_key(self, db_key, PMDU_msg):
        print(f'[Trans] Start monitoring...')
        key_ack = f'{db_key}:ACK'

        retry_count = 0
        waiting_time = 0.0
        waiting_interval = 0.001

        while retry_count < self.c['RETRY_MAX']:
            if self.db.get(self.c['SYSTEM_STATE']).decode('utf-8') == self.c['SYSTEM_TRANS_HOLD']:
                print('System holds')
                return
            elif self.db.get(self.c['MONITOR_ACK']).decode("utf-8") != self.c['ACK_STATE_WAIT']:
                print(f'[Trans] {self.db.get(self.c["MONITOR_ACK"]).decode("utf-8")}')
                # It must receive the ACK
                return
            elif waiting_time <= self.c['WAIT_MAX']:
                print(f'[Trans] {self.db.get(self.c["MONITOR_ACK"]).decode("utf-8")}, {waiting_time} < {self.c["WAIT_MAX"]}, not timeout.')
                # Haven't received the ACK yet, and not timeout yet.
                time.sleep(waiting_interval)
                waiting_time += waiting_interval
            else:
                # Haven't received the ACK and timeout occurs.
                print(f'[Trans] Timeout. Retry [{retry_count+1}/{self.c["RETRY_MAX"]}]')
                retry_count += 1
                waiting_time = 0.0
                p = self.db.pipeline()
                p.delete(f'Trans:{db_key}')
                p.set(f'Trans:{db_key}', PMDU_msg)
                p.execute()
        # Outside the while indicates the retry max is researched.
        # Report Failed
        self.abort_monitor(db_key, key_ack)
        
    def abort_monitor(self, db_key, key_ack):
        print(f'[Trans] ACK status: {self.db.get(self.c["MONITOR_ACK"]).decode("utf-8")}, Abort monitoring...')
        p = self.db.pipeline()
        p.set("RECEPTION", db_key)
        p.set(key_ack, "Failed")
        p.set(self.c['REDEVICE_STATE'], self.c['KEYWORD_IDLE'])
        p.set(self.c['MONITOR_ACK'], self.c['ACK_STATE_FAIL'])
        p.rpop('QUEUE:LIST:TRANS')
        p.execute()
        pass

def main():
    print('Running Transmission Agent...')
    TransAgent('TRANSMISSION', 'AGENT:TRANS')
    pass

if __name__ == '__main__':
    main()  
