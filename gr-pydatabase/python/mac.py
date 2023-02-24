#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2023 gr-pydatabase author.
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


import numpy
import pmt
from gnuradio import gr
import scapy
import sys
import traceback
import json

class mac(gr.basic_block):
    def __init__(self, src_mac, dst_mac, bss_mac):
        gr.basic_block.__init__(self,
            name="mac",
            in_sig=None,
            out_sig=None)
        self.src_mac = src_mac
        self.dst_mac = dst_mac
        self.bss_mac = bss_mac
        
        self.message_port_register_in(pmt.string_to_symbol("app in"))
        self.message_port_register_in(pmt.string_to_symbol("phy in"))
        self.set_msg_handler(pmt.string_to_symbol("app in"), self.app_in)
        self.set_msg_handler(pmt.string_to_symbol("phy in"), self.phy_in)

        self.message_port_register_out(pmt.string_to_symbol("app out"))
        self.message_port_register_out(pmt.string_to_symbol("phy out"))

    def phy_in(self, msg):
        print(f"app_in msg: {msg} type: {type(msg)}")

    def p(self, msg):
        print(f"[WiFi MAC] {msg}")

    def isJSON(self, msg):
        try:
            json.loads(msg)
        except ValueError as e:
            return False
        self.p(f"{msg} is Json")
        return True
    
    def is_mac_valid(self, mac_ary):
        for addr in mac_ary:
            if addr < 0 or addr > 255:
                return False
        return True

    def app_in(self, msg):
        try:
            if pmt.is_pair(msg):
                msdu = pmt.to_python(pmt.car(msg))
                self.p(f'msdu: {msdu}')
            elif pmt.is_symbol(msg):
                msdu = pmt.symbol_to_string(msg)
                self.p(f'msdu: {msdu}')
            else:
                self.p("invalid argument.")
                return

            src_mac = self.src_mac
            dst_mac = self.dst_mac
            bss_mac = self.bss_mac
            if self.isJSON(msdu):
                msdu_json = json.loads(msdu)
                if msdu_json.get("Addresses") is not None:
                    addrs = msdu_json["Addresses"]
                    if addrs.get("SRC") is not None:
                        if self.is_mac_valid(addrs.get("SRC")):
                            src_mac = addrs["SRC"]
                    if addrs.get("DST") is not None:
                        if self.is_mac_valid(addrs.get("DST")):
                            dst_mac = addrs["DST"]
                    if addrs.get("BSS") is not None:
                        if self.is_mac_valid(addrs.get("BSS")):
                            bss_mac = addrs["BSS"]

                self.p(f"msdu_json: {msdu_json}")
            self.p(f"{src_mac} {dst_mac} {bss_mac}")

        except Exception as e:
            print(f"[WiFi MAC] {traceback.print_exc()}")
            return

    def forecast(self, noutput_items, ninput_items_required):
        #setup size of input_items[i] for work call
        for i in range(len(ninput_items_required)):
            ninput_items_required[i] = noutput_items

    def general_work(self, input_items, output_items):
        return False
