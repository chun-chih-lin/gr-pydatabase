import numpy as np
import redis as redis
import utils
import time
import json
import random
import string
import sys, os
import socket
import scapy.all as scapy

from BasicAgent import BasicAgent

class ActionAgent(BasicAgent):
    def __init__(self, subprefix, agentkey):
        super(ActionAgent, self).__init__("ActionAgent", subprefix, agentkey)
        self.init_hop()
        self.tune_gain()
        print('ActionAgent Initialization done.')

    def tune_gain(self):
        if True:
            return
        gain = self.db.hget("TuneRF:11", "Gain").decode("utf-8")
        gain = float(gain)
        if gain > 0.9:
            self.db.hset("TuneRF:11", "Gain", gain-0.1)
        else:
            self.db.hset("TuneRF:11", "Gain", gain+0.1)
        time.sleep(0.01)
        self.db.hset("TuneRF:11", "Gain", gain)
        self.db.set("SYSTEM:ACTION:TUNE", "True", ex=10)

    def agent_event_handler(self, msg):
        try:
            key = self.utf8_decode(msg['channel'])
            if key:
                db_key = self.utf8_decode(self.db.get(self.agentkey))
                if db_key == self.c["KEYWORD_QUIT"]:
                    print('Quiting ActionAgent. See you again.')
                    self.db.set('AGENT:ACTION', self.c["KEYWORD_STOP"])
                    self.thread.stop()
        except Exception as exp:
            print(f'[Action] Exception occurs: {exp}')

    def event_handler(self, msg):
        try:
            # print(f'[Action] Event! {msg}')
            action = self.get_action(msg)
            print(f"[Action] action: {action}")
            if action == self.c["SYSTEM_ACTION_TYPE_CSI"] and msg["data"].decode("utf-8") != "del":
                csi_key = self.db.get(self.c["SYSTEM_ACTION_CSI"]).decode("utf-8")
                timestamp = csi_key.split(":")[1]
                newest_key = self.db.lrange(self.c["SYSTEM_CSI_QUEUE"], 0, 0)
                newest_key = [k.decode("utf-8") for k in newest_key]
                if csi_key in newest_key:
                    # print('key is already in the queue. Skip it.')
                    pass
                elif len(newest_key) < 1:
                    self.db.lpush(self.c["SYSTEM_CSI_QUEUE"], csi_key)
                elif self.is_newer_csi(csi_key, newest_key[0]):
                    self.db.lpush(self.c["SYSTEM_CSI_QUEUE"], csi_key)
                    if len(self.db.lrange(self.c["SYSTEM_CSI_QUEUE"], 0, -1)) > self.c["MAX_CSI_RECORD"]:
                        oldest_csi_key = self.db.rpop(self.c["SYSTEM_CSI_QUEUE"])
                        self.db.delete(oldest_csi_key)
                        # We have enough CSI in the Queue, try to detect the interference.
                        self.detect_interference()
                else:
                    # The key is older somehow. Discard it.
                    self.db.delete(csi_key)
            elif action == self.c["SYSTEM_ACTION_TYPE_HOP"] and msg["data"].decode("utf-8") != "del":
                self.action_to_hop()
            elif action == self.c["SYSTEM_ACTION_TYPE_DEBUG"] and msg["data"].decode("utf-8") != "del":
                self.detect_interference(debug=True)
            elif action == self.c["SYSTEM_ACTION_TYPE_CHECK"]:
                print("Checking")
                if msg["data"].decode("utf-8") != "expired":
                    return

                if self.db.get(self.c["SYSTEM_ACTION_CHECK"]) is not None:
                    print("Not expired yet")
                    return
                
                print(f"Receive ACK?: {self.db.get(self.c['HOPPING_CTRL_ACT_NEW_FREQ_ACK'])}")
                print("After 10 seconds and do not receive anything. Rollback to old freq")
                print("Rolling back...")
                old_freq = self.db.get("SYSTEM:FREQ").decode("utf-8")
                print(f"\tFreq: {old_freq}")
                print(f"\thmset {self.c['TUNE_RF']} {{Freq: {old_freq}}}")
                self.db.hset(self.c['TUNE_RF'], "Freq", old_freq)

                self.release_system()
                return
            elif action == "TUNE":
                if msg["data"].decode("utf-8") == "expired":
                    return
            else:
                print(f"Other action: {action}.")
                        
        except Exception as exp:
            e_type, e_obj, e_tb = sys.exc_info()
            print(f'[Action] Exception occurs: {exp}. At line {e_tb.tb_lineno}')
        
    def is_newer_csi(self, coming_key, newest_key):
        return float(coming_key.split(":")[1]) > float(newest_key.split(":")[1])

    def get_action(self, msg):
        return self.utf8_decode(msg['channel']).split(":")[3]

    def release_system(self):
        self.db.set(self.c["SYSTEM_STATE"], self.c["SYSTEM_FREE"])
        self.db.set(self.c['RFDEVICE_STATE'], self.c["KEYWORD_IDLE"])
        self.init_hop()
    
    def init_hop(self):
        # print(f"[Action] Reset db from hopping.")
        # print("[Action] Should clean all the keys related to the hopping.")
        self.db.delete(self.c["SYSTEM_ACTION_CSI"])
        self.db.delete(self.c["SYSTEM_ACTION_HOP"])
        self.db.delete(self.c["SYSTEM_ACTION_DEBUG"])
        self.db.delete(self.c["HOPPING_CTRL_ACT_NEW_FREQ"])
        self.db.delete(self.c["HOPPING_CTRL_ACT_NEW_FREQ_ACK"])
        self.db.delete(self.c["SYSTEM_ACTION_CHECK"])

    def plan_to_check(self, timeout=None):
        if timeout is None:
            timeout = int(self.c['HOPPING_CTRL_TIMEOUT'])
        print(f"[Action] set {self.c['SYSTEM_ACTION_CHECK']} True ex={timeout}")
        self.db.set(self.c["SYSTEM_ACTION_CHECK"], "True", ex=timeout)

    def is_checking(self):
        return self.db.get(self.c["SYSTEM_ACTION_CHECK"]) is not None

    def hop_successful(self):
        try:
            new_freq = int(self.db.hget(self.c['TUNE_RF'], 'Freq').decode('utf-8'))
            print(f"[Action] Hopping successful. Update the system frequency to {new_freq}")
            self.db.set("LED:HOP:Light", 1)
            csi_keys = self.db.keys("CSI:*")
            for key in csi_keys:
                self.db.delete(key.decode("utf-8"))
            self.db.delete(self.c['SYSTEM_CSI_QUEUE'])
            self.db.set(self.c['SYSTEM_FREQ'], new_freq)
            self.db.delete(self.c["SYSTEM_HOPPING"])
        except Exception as e:
            e_type, e_obj, e_tb = sys.exc_info()
            print(f'[Action] Exception occurs: {e}. At line {e_tb.tb_lineno}')
        pass

    #-------------------------------------------------------------------------------
    def action_to_hop(self):
        try:
            payload = self.db.get("SYSTEM:ACTION:HOP")
            if payload is None:
                print(f'[Action] payload is None. {payload}')
                return

            payload = json.loads(payload.decode("utf-8"))
            if isinstance(payload["ControlAction"], (int, float)):
                if self.is_checking():
                    return
                """ This is on the Follower side
                payload:
                    ControlType: "HOP"
                    ControlAction: hop_to
                    Role: "Follower"
                    Timestamp: timestamp
                    Idx: try_c
                """
                print("[Action] I received hopping request. Trying to reply something back.")
                # Detecting hopping. Jump to new frequency band and starting transmitting ACK back.
                hop_to = payload["ControlAction"]
                pre_freq = self.db.get("SYSTEM:FREQ").decode("utf-8")
                print(f"[Action] Hop to new frequency {hop_to}")
                self.db.hmset(self.c["TUNE_RF"], {"Freq": hop_to})
                print(f"[Action] hmset {self.c['SYSTEM_HOPPING']} Freq {hop_to} PreFreq {pre_freq}")
                self.db.hmset(self.c["SYSTEM_HOPPING"], {"Freq": hop_to, "PreFreq": pre_freq})
                print(f"[Action] sleep for 2.0 second")
                time.sleep(5.0)

                payload["ControlAction"] = "HOP:ACK"
                print(f"[Action] Sendint out {self.c['HOPPING_CTRL_ACT_NOTIFY_NUM']} ACK on new channel. Expecting to receive \"HOP:ACK:ACK\" as response.")
                self.db.set("LED:HOP:Light", 0)
                for i in range(self.c["HOPPING_CTRL_ACT_NOTIFY_NUM"]):
                    new_freq_ack_in_db = self.db.get(self.c['HOPPING_CTRL_ACT_NEW_FREQ_ACK'])
                    print(f"[Action] Sending #{i} action noitify ACK \"HOP:ACK\". {new_freq_ack_in_db}")
                    if new_freq_ack_in_db is not None:
                        print("[Action] receive NEW:FREQ:ACK. Stop sending out HOP:ACK")
                        break
                    self.db.set(self.c["TRANS_FREQ_HOP"], json.dumps(payload))
                    time.sleep(0.1)
                print(f"[Action] Send out all the ACK. Waiting for replay. Expecting to receive \"HOP:ACK:ACK\" as response.")
                self.db.set("LED:HOP:Light", 0)
                self.plan_to_check(timeout=15)
            elif payload["ControlAction"] == "HOP:ACK":
                """ This is on the Initiator side
                payload:
                    ControlType: "HOP"
                    ControlAction: "HOP:ACK"
                """
                print(f"[Action] Receive \"HOP:ACK\" on new channel. Reply \"HOP:ACK:ACK\"")
                self.db.set(self.c["HOPPING_CTRL_ACT_NEW_FREQ_ACK"], "True")
                payload["ControlAction"] = "HOP:ACK:ACK"
                time.sleep(5.0)
                for i in range(30):
                    print(f"[Action] Reply HOP:ACK:ACK. Sending #{i} {payload}")
                    self.db.set(self.c["TRANS_FREQ_HOP"], json.dumps(payload))
                    time.sleep(0.2)
                print(f"[Action] Send out all the ACK:ACK.")
                self.release_system()
                self.hop_successful()
                
            elif payload["ControlAction"] == "HOP:ACK:ACK":
                """ This is on the Follower side
                payload:
                    ControlType: "HOP"
                    ControlAction: "HOP:ACK:ACK"
                """
                self.db.set(self.c["HOPPING_CTRL_ACT_NEW_FREQ_ACK"], "True")
                print(f"[Action] Receive HOP:ACK:ACK on new channel")
                self.release_system()
                self.hop_successful()
            else:
                return
        except Exception as e:
            _, _, e_tb = sys.exc_info()
            print(f'[ActionAgent] {e}, Line {e_tb.tb_lineno}')
        pass

    #--------------------------------------------------------------------------------
    # For Action: Detecting Interference
    def get_all_csi_in_db(self):
        try:
            csi_keys_list = self.db.lrange(self.c["SYSTEM_CSI_QUEUE"], 0, -1)
            csi_list = []
            for csi_key in csi_keys_list:
                print(f'csi_key: {csi_key}')
                csi_json_str = self.db.get(csi_key).decode('utf-8')
                csi_json = json.loads(csi_json_str)
                csi = np.array(csi_json['real']) + 1j*np.array(csi_json['imag'])
                csi_list.append(csi)
        except Exception as exp:
            _, _, e_tb = sys.exc_info()
            print(f'[Action] get_all_csi_in_db: {exp}. At line {e_tb.tb_lineno}')
        return np.array(csi_list)

    def sliding_var_detect(self, csis):
        sliding_detect_csis = np.zeros((csis.shape[0],csis.shape[1]-self.sliding_window_size))
        for csi_i, csi in enumerate(csis):
            ret = []
            for i, s in enumerate(csi[:len(csi)-self.sliding_window_size]):
                ret.append(np.mean(np.var(csi[i:i+self.sliding_window_size])))
            sliding_detect_csis[csi_i, :] = ret
        return sliding_detect_csis
        
    def median_max_detect(self, sliding_var_ary):
        median_max_detection = []
        for d_i, d in enumerate(sliding_var_ary):
            median = np.median(d)
            max_v = np.max(d)
            if median == 0:
                median_max_detection.append(0)
            elif max_v/median > self.median_threshold:
                median_max_detection.append(1)
            else:
                median_max_detection.append(0)
        return median_max_detection

    def consecutive_detect(self, detections):
        consecutive_detection = [a*b for (a, b) in zip(detections[:-1], detections[1:])]
        return consecutive_detection

    def detect_interference(self, debug=False):
        try:
            print('[Action] Detecting interference...')

            # TODO: Setting should be set in db for dynamic changes
            self.sliding_window_size = 4
            self.median_threshold = 5.0
            self.consecutive_threshold = 3

            FAILRED = '\033[91m'
            OKGREEN = '\033[92m'
            WARNING = '\033[93m'
            EOC = '\033[0m'
            csi_list = self.get_all_csi_in_db()
            if len(csi_list) == 0:
                detections = []
            else:
                sliding_var_detect_csis = self.sliding_var_detect(csi_list)
                detections = self.median_max_detect(sliding_var_detect_csis)
            print(f'[Action] detections: {detections}')
            consecutive_detection = self.consecutive_detect(detections)
            print(f'[Action] consecutive_detection: {consecutive_detection}')
            print(f'[Action] sum: {sum(consecutive_detection)}, threshold: {self.consecutive_threshold}, debug: {debug}')

            if sum(consecutive_detection) >= self.consecutive_threshold or debug:
                # On Detected, Stage 1.
                print(f'Too many detected! ({sum(consecutive_detection)}/{len(consecutive_detection)}) Interference detected!')
                # print('Hold the system and try to initiate to jump to another frequency with the receiver.')
                # print('Hold the transmission process')
                # Hold the system, Stage 2.
                # self.db.hset(self.c["SYSTEM_HOPPING"], "Stage", 2)
                self.db.set(self.c["SYSTEM_STATE"], self.c["SYSTEM_TRANS_HOLD"])

                # Initiating the attempt, Stage 3.
                current_freq = int(self.db.get(self.c['SYSTEM_FREQ']).decode("utf-8"))
                print(f"[Action] Channels: {self.c['DOT_11_CHANNELS'].copy()}")
                print(f"[Aciton] I'm using {current_freq} {type(current_freq)}...")
                options = [int(f) for f in self.c['DOT_11_CHANNELS'] if int(f) != current_freq]
                hop_to = options[0]
                print(f"[Action] hop_to: {hop_to}")
                
                ctrl_msg = dict()
                ctrl_msg["ControlType"] = "HOP"
                ctrl_msg["ControlAction"] = hop_to
                ctrl_msg["Role"] = "Follower"

                pre_freq = self.db.get("SYSTEM:FREQ").decode("utf-8")

                for try_c in range(self.c["HOPPING_CTRL_ACT_NOTIFY_NUM"]):
                    timestamp = time.time()
                    ctrl_msg["Timestamp"] = timestamp
                    ctrl_msg["Idx"] = try_c
                    json_info = json.dumps(ctrl_msg, separators=(',', ':'))
                    self.db.hmset(self.c["SYSTEM_HOPPING"], {"Role": "Initiator", "Stage": 3, "Freq": hop_to, "PreFreq": pre_freq})
                    if try_c == 0:
                        self.db.hset(self.c["SYSTEM_HOPPING"], "Timestamp", timestamp)
                    self.db.set(self.c["TRANS_FREQ_HOP"], json_info)
                    time.sleep(0.1)

                self.db.hmset(self.c["TUNE_RF"], {"Freq": hop_to})
                self.db.set(self.c['HOPPING_CTRL_ACT_NEW_FREQ_ACK'], "Wait")
                print(f"[Action] I initiate the frequency hopping. Wait for 30 seconds and see if anyone get some response.")
                self.plan_to_check(timeout=30)

        except Exception as exp:
            e_type, e_obj, e_tb = sys.exc_info()
            print(f"[Action] Detecting Interference {exp}. At line {e_tb.tb_lineno}")

def main():
    print('Running Action Agent...')
    ActionAgent('SYSTEM:ACTION:*', 'AGENT:ACTION')

if __name__ == "__main__":
    main()
