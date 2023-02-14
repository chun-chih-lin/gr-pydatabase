#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2022 gr-pydatabase author.
#
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#

import redis
import pmt
import json
import time

import socket
import scapy.all as scapy

import sys

import numpy
from gnuradio import gr

class redis_sink(gr.sync_block):
    """
    doc string for block redis_sink
    """
    def __init__(self, db_ch, db_port, db_host, db_idx, macaddr, debug):
        gr.sync_block.__init__(self,
            name="redis_sink",
            in_sig=None,
            out_sig=None)

        self.debug = debug
        self.db_ch = db_ch
        self.db_port = db_port
        self.db_host = db_host
        self.db_idx = db_idx

        self.redis_db = redis.Redis(host=self.db_host, port=self.db_port, db=self.db_idx)
        self.pipeline = self.redis_db.pipeline()

        self.macaddr = macaddr or self.redis_db.get("SELF:MACADDR").decode("utf-8")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.FRMAE_MGMT = 0
        self.FRMAE_CTRL = 1
        self.FRMAE_DATA = 2

        self.MONITOR_ACK = "TRANS:ACK"
        self.ACK_STATE_WAIT = "Waiting"
        self.ACK_STATE_FAIL = "Failed"
        self.ACK_STATE_SUCC = "Success"
        self.REDEVICE_STATE = "RFDEVICE:STATE"
        self.KEYWORD_QUIT = "Quit"
        self.KEYWORD_BUSY = "Busy"
        self.KEYWORD_IDLE = "Idle"
        self.KEYWORD_STOP = "Stop"
        self.KEYWORD_WAIT_ACK = "WAITACK"
        self.QUEUE_NAME = "QUEUE:LIST:TRANS"

        self.message_port_register_in(pmt.string_to_symbol("pdu"))
        self.set_msg_handler(pmt.string_to_symbol("pdu"), self.parse_pdu_into_db)

    def msg_debug(self, s):
        if self.debug:
            print(s)
        pass

    def parse_pdu_into_db(self, pdu):
        def check_dest(addr):
            # self.msg_debug(f'{self.macaddr}, {addr}')
            return self.macaddr == addr
        def get_type(frame_type, frame_subtype):
            if frame_type == 0:
                frame_type_str = "Management"
                frame_subtype_str = get_subtype_mgmt(frame_subtype)
            elif frame_type == 1:
                frame_type_str = "Control"
                frame_subtype_str = get_subtype_ctrl(frame_subtype)
            elif frame_type == 2:
                frame_type_str = "Data"
                frame_subtype_str = get_subtype_data(frame_subtype)
            else:
                frame_type_str = "Extension"
                frame_subtype_str = get_subtype_extn(frame_subtype)
            return frame_type_str, frame_subtype_str
        def parse_header(header_vector):
            hex_list = [hex(i) for i in header_vector]

            frame_ctrl = str(hex_list[0])
            frame_ctrl_bin = format(int(frame_ctrl, 16), "08b")

            frame_subtype = int(frame_ctrl_bin[:4], 2)
            frame_type = int(frame_ctrl_bin[4:6], 2)
            version = int(frame_ctrl_bin[6:], 2)

            frame_type_str, frame_subtype_str = get_type(frame_type, frame_subtype)
            duration = int(header_vector[2] + header_vector[3])

            addr1 = ":".join(["{:02x}".format(int(i, 16)) for i in hex_list[4:10]])
            addr2 = ":".join(["{:02x}".format(int(i, 16)) for i in hex_list[10:16]])
            addr3 = ":".join(["{:02x}".format(int(i, 16)) for i in hex_list[16:22]])

            header_dict = dict()
            header_dict["subtype"] = frame_subtype
            header_dict["type"] = frame_type
            header_dict["version"] = version
            header_dict["duration"] = duration
            header_dict["addr1"] = addr1        # Receiver
            header_dict["addr2"] = addr2        # Sender
            header_dict["addr3"] = addr3        # Filtering
            header_dict["type_str"] = frame_type_str
            header_dict["subtype_str"] = frame_subtype_str

            # header_json = json.dumps(header_dict)
            return check_dest(addr1), header_dict, frame_type_str
        def get_subtype_mgmt(subtype):
            switcher = {
                0: "Association Request",
                1: "Association Response",
                2: "Reassociation Request",
                3: "Reassociation Response",
                4: "Probe Request",
                5: "Probe Response",
                6: "Timing Advertisement",
                7: "Reserved",
                8: "Beacon",
                9: "ATIM",
                10: "Disassociation",
                11: "Authentication",
                12: "Deauthentication",
                13: "Action",
                14: "Action No Ack (NACK)",
                15: "Reserved",
            }
            return switcher.get(subtype, "Unknown")
        def get_subtype_ctrl(subtype):
            switcher = {
                0: "Reserved",
                1: "Reserved",
                2: "Trigger",
                3: "TACK",
                4: "Beamforming Report Poll",
                5: "VHT/HE NDP Announcement",
                6: "Control Frame Extension",
                7: "Control Wrapper",
                8: "Block Ack Request (BAR)",
                9: "Block Ack (BA)",
                10: "PS-Poll",
                11: "RTS",
                12: "CTS",
                13: "ACK",
                14: "CF-End",
                15: "CF-End + CF-ACK",
            }
            return switcher.get(subtype, "Unknown")
        def get_subtype_data(subtype):
            switcher = {
                0: "Data",
                1: "Reserved",
                2: "Reserved",
                3: "Reserved",
                4: "Null (no data)",
                5: "Reserved",
                6: "Reserved",
                7: "Reserved",
                8: "QoS Data",
                9: "QoS Data + CF-ACK",
                10: "QoS Data + CF-Poll",
                11: "QoS Data + CF-ACK + CF-Poll",
                12: "QoS Null (no data)",
                13: "Reserved",
                14: "QoS CF-Poll (no data)",
                15: "QoS CF-ACK + CF-Poll (no data)",
            }
            return switcher.get(subtype, "Unknown")
        def get_subtype_extn(subtype):
            switcher = {
                0: "DMG Beacon",
                1: "S1G Beacon",
            }
            return switcher.get(subtype, "Reserved")

        # Check if pdu is PDU
        # self.msg_debug("[gr-pydatabase] Check if pdu is PDU...")
        try:
            if pmt.is_pair(pdu):

                # self.msg_debug("[gr-pydatabase] It is a PDU!")
                meta = pmt.to_python(pmt.car(pdu))
                if meta is None:
                    meta = dict()

                vector = pmt.cdr(pdu)
                pmt_vector = pmt.to_python(vector)
                payload = ""

                if pmt.is_u8vector(vector):
                    vector = pmt.u8vector_elements(vector)
                    payload = "".join([chr(r) for r in vector[24:]])
                    if len(payload) == 0:
                        return
                                        
                    ### header_info: for future used as indication for the receiver and transmitter
                    is_for_me, header_info, frame_type = parse_header(pmt_vector)
                    self.msg_debug(f'header_info: \n{header_info}')
                    self.msg_debug(f'payload: {payload}')
                    self.msg_debug(f'Receive a type: {header_info["type"]} frame')
                    if is_for_me:
                        payload_dict = json.loads(payload)
                        print(f"[Sink] payload: {payload}")
                        if payload_dict.get('ControlType') is not None:
                            # It is a control data frame.
                            if payload_dict['ControlType'] == "HOP":
                                print("Hold the system until hopping is completed")
                                if payload_dict["ControlAction"].isdigit():
                                    print("set RFSYSTEM:STATE Hold")
                                    print("hset SYSTEM:HOPPING Stage 4")
                                    self.redis_db.set("RFSYSTEM:STATE", "Hold")
                                    self.redis_db.hset("SYSTEM:HOPPING", "Stage", 4)
                                self.action_to_hop(payload)
                            return
                            self.msg_debug('If it is a ControlType frame, this line should not be executed')
                        # ---------------------
                        real_csi = meta['csi'].real.tolist()
                        imag_csi = meta['csi'].imag.tolist()
                        meta.pop('csi', None)
                        meta['real'] = real_csi
                        meta['imag'] = imag_csi

                        csi_dict = dict()
                        csi_dict['real'] = real_csi
                        csi_dict['imag'] = imag_csi
                        csi_json = json.dumps(csi_dict)

                        if header_info['type'] == self.FRMAE_DATA:
                            info_json = json.dumps(meta)
                            csi_json = json.dumps(csi_dict)
                            self.msg_debug(f'It is for me. header_info["type"]: {header_info["type"]}')
                            self.msg_debug(f'It is for me. header_info["subtype"]: {header_info["subtype"]}')
                            # Only write the data to db if it is a DATA frame
                            self.msg_debug(f'Receive a DATA frame')
                            self.reply_with_ack(header_info['addr2'])
                            self.set_to_db(payload, info_json, csi_json)
                        else:
                            # Someone just replied a ACK to me
                            if header_info['type'] == self.FRMAE_CTRL and header_info['subtype'] == 13:
                                self.action_to_ack()
                    else:
                        # The destination is not me. Discard the received pkt.
                        # self.msg_debug('header_info:\n', header_info)
                        self.msg_debug(f'It is not for me. Send to {header_info["addr1"]}, I\'m {self.macaddr}')
        except Exception as exp:
            e_type, e_obj, e_tb = sys.exc_info()
            self.pipeline.reset()
            print(f'[redis sink] Exception: {exp}. At line {e_tb.tb_lineno}')
        self.pipeline.execute()
        self.pipeline.reset()
        pass

    def action_to_hop(self, payload):
        print(f'action to hop {payload}')
        self.redis_db.set("SYSTEM:ACTION:HOP", payload)
        pass


    def action_to_ack(self):
        ACK_status = self.redis_db.get(self.MONITOR_ACK)
        self.msg_debug(f'[Redis_sink] ACK Status: {ACK_status.decode("utf-8")}')
        if ACK_status.decode('utf-8') == self.ACK_STATE_WAIT:
            self.msg_debug('[Redis_sink] Receive ACK.')
            p = self.redis_db.pipeline()
            p.set(self.MONITOR_ACK, self.ACK_STATE_SUCC)
            p.set(self.REDEVICE_STATE, self.KEYWORD_IDLE)
            p.rpop(self.QUEUE_NAME)
            p.execute()
            p.reset()
            self.msg_debug('[Redis_sink] RPOP. Can start the next msg...')
        else:
            self.msg_debug('[Redis_sink] Receive redundent ACK...')

    def get_info_from_vector(self, pmt_vector, start_pos, length):
        data = "".join([chr(r) for r in pmt_vector[start_pos:start_pos+length]])
        return data

    def reply_with_ack(self, addr):
        self.msg_debug(f'[Redis_sink] Receive a DATA frame. Reply with ACK to address: {addr}')
        ack_frame = scapy.Dot11FCS(addr1=addr, type=1, subtype=13, FCfield=0)
        self.sock.sendto(bytes(ack_frame), ("127.0.0.1", 52001))
        pass

    def set_to_db(self, payload, info_json, csi_json):
        # self.msg_debug("[gr-pydatabase] Parsing the payload and set the information to db...")
        try:
            seq = json.loads(payload)['sequence']
            set_key = f'Recv:{seq}'
            self.msg_debug(f'[Redis_sink] keys: {set_key+":*"}, result: {self.redis_db.keys(set_key+":*")}')
            if self.redis_db.keys(set_key + ':*'):
                # Already in db
                self.msg_debug(f'[Redis_sink] key {set_key+":*"}, Already in db')
            else:
                self.pipeline.hmset(f'Recv:{seq}:{str(time.time())}', {'payload': payload, 'info': info_json})

            timestamp = str(time.time())
            self.pipeline.set(f'CSI:{timestamp}', csi_json)
            self.pipeline.set("SYSTEM:ACTION:CSI", f'CSI:{timestamp}')
        except Exception as exp:
            self.msg_debug(f'[Redis_sink] Exception: set_to_db {exp}')
            self.msg_debug(f'[Redis_sink] Exception: payload:\n', payload, '\ninfo:\n', info_json)
        pass

    def work(self, input_items, output_items):
        return False

