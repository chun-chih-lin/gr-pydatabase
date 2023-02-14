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
        print('Initialization done.')

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
            print(f'[Action] Event! {msg}')
            action = self.get_action(msg)
            print(f"[Action] action: {action}")
            print(f"Config: {self.c}")
            if action == self.c["SYSTEM_ACTION_TYPE_CSI"]:
                csi_key = self.db.get(self.c["SYSTEM_ACTION_CSI"]).decode("utf-8")
                timestamp = csi_key.split(":")[1]
                newest_key = self.db.lrange(self.c["SYSTEM_CSI_QUEUE"], 0, 0)
                newest_key = [k.decode("utf-8") for k in newest_key]
                if csi_key in newest_key:
                    print('key is already in the queue. Skip it.')
                    pass
                elif len(newest_key) < 1:
                    self.db.lpush(self.c["SYSTEM_CSI_QUEUE"], csi_key)
                elif self.is_newer_csi(csi_key, newest_key[0]):
                    self.db.lpush(self.c["SYSTEM_CSI_QUEUE"], csi_key)
                    if len(self.db.lrange(self.c["SYSTEM_CSI_QUEUE"], 0, -1)) > self.c["MAX_CSI_RECORD"]:
                        oldest_csi_key = self.db.rpop(self.c["SYSTEM_CSI_QUEUE"])
                        print(f'Adding new key: {csi_key}. Delete oldest key: {oldest_csi_key}')
                        print(f'*** db.delete({oldest_csi_key})')
                        self.db.delete(oldest_csi_key)
                        # We have enough CSI in the Queue, try to detect the interference.
                        self.detect_interference()
                else:
                    # The key is older somehow. Discard it.
                    print(f'incoming key: {csi_key} is older somehow, discard it.')
                    print(f'keys in queue: {newest_key}')
                    print(f'*** db.delete({csi_key})')
                    self.db.delete(csi_key)
            elif action == self.c["SYSTEM_ACTION_TYPE_HOP"]:
                self.action_to_hop()
            elif action == self.c["SYSTEM_ACTION_TYPE_DEBUG"]:
                self.detect_interference(debug=True)
            elif action == self.c["SYSTEM_ACTION_TYPE_CHECK"]:
                print("Checking")

            else:
                print(f"Other action: {aciton}.")
                        
        except Exception as exp:
            e_type, e_obj, e_tb = sys.exc_info()
            print(f'[Action] Exception occurs: {exp}. At line {e_tb.tb_lineno}')
        
    def is_newer_csi(self, coming_key, newest_key):
        return float(coming_key.split(":")[1]) > float(newest_key.split(":")[1])

    def get_action(self, msg):
        return self.utf8_decode(msg['channel']).split(":")[3]

    #-------------------------------------------------------------------------------
    def action_to_hop(self):
        try:
            payload = self.db.get("SYSTEM:ACTION:HOP").decode("utf-8")
            payload = json.loads(payload)

            role = self.db.hget(self.c["SYSTEM_HOPPING"], "Role")
            if role is None:
                self.db.hset(self.c["SYSTEM_HOPPING"], "Role", payload["Role"])
            else:
                role = role.decode("utf-8")

            msg = dict()
            msg["ControlType"] = self.c["SYSTEM_ACTION_TYPE_HOP"]
            stage = self.db.hget(self.c["SYSTEM_HOPPING"], "Stage").decode("utf-8")

            p = self.db.pipeline()

            print("---------------------------------")
            if role == self.c["SYSTEM_HOPPING_ROLE_INIT"]:
                # I'm initiating the hopping
                print(f"I'm an initiator. Stage: {stage}")
                if payload["ControlAction"] == self.c["HOPPING_CTRL_ACT_HOLD_ACK"] and stage == "3":
                    
                    hop_to = self.db.hget(self.c["SYSTEM_HOPPING"], "Freq").decode("utf-8")
                    p.hmset(self.c["TUNE_RF"], {"Freq": hop_to, "Gain": 0.4})
                    p.hset(self.c["SYSTEM_HOPPING"], "Stage", 7)
                    p.execute()
                    p.reset()
                    print(f"Using the new frequency!")
                    print(f"  hset {self.c['TUNE_RF']} Freq {hop_to}")
                    print(f"  hset {self.c['TUNE_RF']} Gain 0.4")
                    print(f"  hset {self.c['SYSTEM_HOPPING']} Stage 7")


                    print("Send 5 check packets on new channel")
                    for try_c in range(5):
                        msg["ControlAction"] = self.c["HOPPING_CTRL_ACT_NEW_FREQ"]
                        p.set(self.c["TRANS_FREQ_HOP"], json.dumps(msg))
                        p.hset(self.c["SYSTEM_HOPPING"], "Stage", 8)
                        print("Sending out the check on new channel...")
                        print(f"  set {self.c['TRANS_FREQ_HOP']}, {msg}")
                        print(f"  hset {self.c['SYSTEM_HOPPING']} Stage 8")
                        p.execute()
                        p.reset()
                        time.sleep(0.01)
                    return
                elif payload["ControlAction"] == self.c["HOPPING_CTRL_ACT_NEW_FREQ_ACK"] and stage == '8':
                    print("Receive NEW:FREQ:ACK")
                    p.set(self.c["SYSTEM_STATE"], self.c["SYSTEM_FREE"])
                    p.execute()
                    p.reset()
                    return
                else:
                    print("Something went wrong.")
                    print(f"Role: {role} {type(role)}, Stage: {stage}")
                    return
            else:
                # I'm the follower.
                print(f"I'm a follower, {stage}")
                if stage == '4':
                    pre_freq = self.db.get(self.c["SYSTEM_FREQ"]).decode("utf-8")
                    
                    msg["ControlAction"] = self.c["HOPPING_CTRL_ACT_HOLD_ACK"]
                    p.set(self.c["TRANS_FREQ_HOP"], json.dumps(msg))
                    p.hset(self.c["SYSTEM_HOPPING"], "Stage", 5)
                    p.execute()
                    p.reset()
                    print(f"Received the initiation, send back the hold ack")
                    print(f"  set {self.c['TRANS_FREQ_HOP']}, {msg}")
                    print(f"  hset {self.c['SYSTEM_HOPPING']} Stage 5")


                    print(f"  Timestamp: {payload['Timestamp']}, Idx: {payload['Idx']}")
                    wait_time = 0
                    #wait_time = payload["Timestamp"] + 0.01*float(payload["Idx"]) - time.time()
                    wait_time += 0.15
                    print(f"Wait for {wait_time} to change the freq")
                    time.sleep(wait_time)
                    print("Switch to new Freq")
                    p.hmset(self.c["TUNE_RF"], {"Freq": payload["ControlAction"], "Gain": 0.4})
                    p.hmset(self.c["SYSTEM_HOPPING"], {"Stage": 6, "PreFreq": pre_freq, "Freq": payload["ControlAction"]})
                    print(f"Change to new channel {payload['ControlAction']}")
                    print(f"  hset {self.c['TUNE_RF']} Freq {payload['ControlAction']}")
                    print(f"  hset {self.c['TUNE_RF']} Gain 0.4")
                    print(f"  hset {self.c['SYSTEM_HOPPING']} Stage 6")
                    print(f"  hset {self.c['SYSTEM_HOPPING']} PreFreq {pre_freq}")
                    print(f"  hset {self.c['SYSTEM_HOPPING']} Freq {payload['ControlAction']}")
                    p.execute()
                    p.reset()
                    return
                elif stage == '6':
                    for try_c in range(5):
                        msg["ControlAction"] = self.c["HOPPING_CTRL_ACT_NEW_FREQ_ACK"]
                        p.set(self.c["TRANS_FREQ_HOP"], json.dumps(msg))
                        p.hset(self.c["SYSTEM_HOPPING"], "Stage", 9)
                        print("Reply NEW:FREQ:ACK")
                        print(f"  set {self.c['TRANS_FREQ_HOP']}, {json.dumps(msg)}")
                        print(f"  hset {self.c['SYSTEM_HOPPING']}, Stage 9")
                        p.execute()
                        p.reset()
                        time.sleep(0.01)

                    time.sleep(0.5)
                    self.db.set(self.c["SYSTEM_STATE"], self.c["SYSTEM_FREE"])
                    return
                else:
                    print("Something went wrong.")
                    print(f"Role: {role}, Stage: {stage}")
                    return
        except Exception as exp:
            _, _, e_tb = sys.exc_info()
            print(f'[ActionAgent] {exp}, Line {e_tb.tb_lineno}')
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

            print(f'{len(csi_list)}')

            sliding_var_detect_csis = self.sliding_var_detect(csi_list)
            detections = self.median_max_detect(sliding_var_detect_csis)
            print(f'detections: {detections}')
            consecutive_detection = self.consecutive_detect(detections)
            print(f'consecutive_detection: {consecutive_detection}')

            print(f'sum: {sum(consecutive_detection)}, threshold: {self.consecutive_threshold}, debug: {debug}')

            if sum(consecutive_detection) >= self.consecutive_threshold or debug:
                # On Detected, Stage 1.
                print(f'Too many detected! ({sum(consecutive_detection)}/{len(consecutive_detection)}) Interference detected!')
                print('Hold the system and try to initiate to jump to another frequency with the receiver.')
                print('Hold the transmission process')
                # Hold the system, Stage 2.
                self.db.hset(self.c["SYSTEM_HOPPING"], "Stage", 2)
                self.db.set(self.c["SYSTEM_STATE"], self.c["SYSTEM_TRANS_HOLD"])

                # Initiating the attempt, Stage 3.
                hop_to = "2442000000"
                ctrl_msg = dict()
                ctrl_msg["ControlType"] = "HOP"
                ctrl_msg["ControlAction"] = hop_to
                ctrl_msg["Role"] = "Follower"

                pre_freq = self.db.get("SYSTEM:FREQ").decode("utf-8")

                for try_c in range(5):
                    timestamp = time.time()
                    ctrl_msg["Timestamp"] = timestamp
                    ctrl_msg["Idx"] = try_c
                    json_info = json.dumps(ctrl_msg, separators=(',', ':'))
                    self.db.hmset("SYSTEM:HOPPING", {"Role": "Initiator", "Stage": 3, "Freq": hop_to, "PreFreq": pre_freq})
                    if try_c == 0:
                        self.db.hset("SYSTEM:HOPPING", "Timestamp", timestamp)
                    self.db.set(self.c["TRANS_FREQ_HOP"], json_info)
                    print(f"hset SYSTEM:HOPPING  Role Initiator")
                    print(f"hset SYSTEM:HOPPING  Stage 3")
                    print(f"hset SYSTEM:HOPPING  Freq {hop_to}")
                    print(f"hset SYSTEM:HOPPING  PreFreq {pre_freq}")
                    print(f"set {self.c['TRANS_FREQ_HOP']} {json_info}")
                    time.sleep(0.01)

                print(f"Send out five packets, switch to new channel...")
                self.db.hmset(self.c["TUNE_RF"], {"Freq": hop_to, "Gain": 0.4})

                print(f"Set 10 second timeout check")
                self.db.set(self.c["SYSTEM_ACTION_CHECK"], "True")
                self.db.expire(self.c["SYSTEM_ACTION_CHECK"], 10)
                print(f"expire {self.c['SYSTEM_ACTION_CHECK']} 10")

        except Exception as exp:
            e_type, e_obj, e_tb = sys.exc_info()
            print(f"[Action] Detecting Interference {exp}. At line {e_tb.tb_lineno}")

def main():
    print('Running Action Agent...')
    ActionAgent('SYSTEM:ACTION:*', 'AGENT:ACTION')

if __name__ == "__main__":
    main()
