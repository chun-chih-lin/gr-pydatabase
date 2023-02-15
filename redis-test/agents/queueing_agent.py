import numpy as np
import redis as redis
import utils
import time
import json
import random
import string
import sys, os

from BasicAgent import BasicAgent

class QueueAgent(BasicAgent):
    def __init__(self, subprefix, agentkey):
        super(QueueAgent, self).__init__("QueueAgent", subprefix, agentkey)
        self.db.set(self.c["FAIL_ACK_NUM"], 0)
        print('Initialization done.')

    def agent_event_handler(self, msg):
        try:
            key = self.utf8_decode(msg["channel"])
            if key:
                db_key = self.utf8_decode(self.db.get(self.agentkey))
                if db_key == self.c['KEYWORD_QUIT']:
                    print('Quiting QueueAgent. See you again.')
                    self.db.set('AGENT:QUEUE', self.c['KEYWORD_STOP'])
                    self.thread.stop()
        except Exception as exp:
            _, _, e_tb = sys.exc_info()
            print(f'[Queue] Exception occurs: {exp}, Line {e_tb.tb_lineno}')

    def event_handler(self, msg):
        try:
            key = self.utf8_decode(msg["channel"])
            if key:
                # get the db_key for transmission information
                db_key = "QUEUE:LIST:TRANS"
                self.process_message(db_key)
        except Exception as exp:
            _, _, e_tb = sys.exc_info()
            print(f'[Queue] Exception occurs: {exp}, Line {e_tb.tb_lineno}')

    def process_message(self, db_key):
        try:
            while self.db.exists(db_key):
                # While "QUEUE:LIST:TRANS" exist, means there is message needs to be transmitted
                print(f"[Queue] {self.db.get(self.c['RFDEVICE_STATE'])}")
                rf_device_state = self.utf8_decode(self.db.get(self.c['RFDEVICE_STATE']))
                print(f"[Queue] RF state: {rf_device_state}")
                oldest_key = self.utf8_decode(self.db.lrange(db_key, -1, -1)[0])
                print(f"[Queue] Processing for key: {oldest_key}")
                ack_for_key = self.db.get(f"{oldest_key}:ACK")
                print(f"[Queue] ACK for the key: {ack_for_key}")
                if ack_for_key is not None:
                    if ack_for_key.decode("utf-8") == "Failed":
                        print("It is failed, pop it.")
                        self.db.rpop(db_key)
                        self.db.incr(self.c["FAIL_ACK_NUM"])
                        if self.db.get(self.c["FAIL_ACK_NUM"]).decode("utf-8") >= 20:
                            time.sleep(0.2)
                            self.db.set(self.c["FAIL_ACK_NUM"], 0)

                
                elif rf_device_state == self.c['KEYWORD_IDLE']:
                    # There are some keys in the queue and the RF is Idle.
                    oldest_key = self.utf8_decode(self.db.lrange(db_key, -1, -1)[0])
                    # Trigger the Transmission Agent to transmit
                    # Set the state of RF as Busy
                    p = self.db.pipeline()
                    # Tell the transmission agent which key to be transmitted
                    # print(f'Tell transmission agent to trans {oldest_key}')
                    p.set(self.c['KEYWORD_TRANS'], oldest_key)
                    # Set rf device to Busy
                    p.set(self.c['RFDEVICE_STATE'], self.c['KEYWORD_BUSY'])
                    p.execute()
                    p.reset()
                elif self.db.get(self.c['SYSTEM_STATE']).decode('utf-8') == self.c['SYSTEM_TRANS_HOLD']:
                    print("[Queue] System Holding")
                    time.sleep(0.4)
                else:
                    print('[Queue] Still processing, sleep for 0.001 second.')
                    time.sleep(0.001)
                print('Done processing all the msg in queue')
        except Exception as exp:
            _, _, e_tb = sys.exc_info()
            print(f'[Queue] Exception occurs: {exp}, Line {e_tb.tb_lineno}')


def main():
    QueueAgent('QUEUE:LIST:TRANS', 'AGENT:QUEUE')

if __name__ == '__main__':
    main()
