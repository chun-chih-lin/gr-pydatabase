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

import numpy
from gnuradio import gr

class redis_sink(gr.sync_block):
    """
    doc string for block redis_sink
    """
    def __init__(self, db_ch, db_port, db_host, db_idx):
        gr.sync_block.__init__(self,
            name="redis_sink",
            in_sig=None,
            out_sig=None)

        self.db_ch = db_ch
        self.db_port = db_port
        self.db_host = db_host
        self.db_idx = db_idx

        self.redis_db = redis.Redis(host=self.db_host, port=self.db_port, db=self.db_idx)

        self.message_port_register_in(pmt.string_to_symbol("pdu"))
        self.set_msg_handler(pmt.string_to_symbol("pdu"), self.parse_pdu_into_db)

    def parse_pdu_into_db(self, pdu):
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

            frame_ctrl = "0x" + str(header_vector[0]) + str(header_vector[1])
            frame_ctrl_bin = format(int(frame_ctrl, 16), "08b")

            frame_subtype = int(frame_ctrl_bin[4:], 2)
            frame_type = int(frame_ctrl_bin[:2], 2)
            version = int(frame_ctrl_bin[2:4], 2)
            frame_type_str = get_type(frame_type, frame_subtype)
            duration = int(header_vector[2] + header_vector[3])
            addr1 = ":".join([i.lstrip("0x") for i in hex_list[4:10]])
            addr2 = ":".join([i.lstrip("0x") for i in hex_list[10:16]])
            addr3 = ":".join([i.lstrip("0x") for i in hex_list[16:22]])

            header_dict = dict()
            header_dict["frame_subtype"] = frame_subtype
            header_dict["frame_type"] = frame_type
            header_dict["version"] = version
            header_dict["duration"] = duration
            header_dict["addr1"] = addr1
            header_dict["addr2"] = addr2
            header_dict["addr3"] = addr3

            header_json = json.dumps(header_dict)
            return header_json
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
        # print("[gr-pydatabase] Check if pdu is PDU...")
        if pmt.is_pair(pdu):
            # print("[gr-pydatabase] It is a PDU!")
            meta = pmt.to_python(pmt.car(pdu))
            if meta is None:
                meta = dict()

            vector = pmt.cdr(pdu)
            pmt_vector = pmt.to_python(vector)
            payload = ""
            if pmt.is_u8vector(vector):
                vector = pmt.u8vector_elements(vector)
                payload = "".join([chr(r) for r in vector[24:]])
                # print("[gr-pydatabase] payload: ", payload)
                header_info = parse_header(pmt_vector)
                # print("[gr-pydatabase] header_info: ", header_info)
                # self.parse_header(vector)
                self.set_to_db(payload)
        pass

    def get_info_from_vector(self, pmt_vector, start_pos, length):
        data = "".join([chr(r) for r in pmt_vector[start_pos:start_pos+length]])
        return data

    def set_to_db(self, payload):
        # print("[gr-pydatabase] Parsing the payload and set the information to db...")
        # print("[gr-pydatabase] payload: ", payload)
        self.redis_db.set("Recv:" + time.time(), payload)
        pass

    def work(self, input_items, output_items):
        return False

