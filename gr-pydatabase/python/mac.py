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

import pmt
import numpy
from gnuradio import gr

class mac(gr.sync_block):
    """
    docstring for block mac
    """
    def __init__(self, src_mac, dst_mac, bss_mac):
        gr.sync_block.__init__(self,
            name="mac",
            in_sig=None,
            out_sig=None)
        self.src_mac = src_mac
        self.dst_mac = dst_mac
        self.bss_mac = bss_mac

        self.MAX_PAYLOAD_SIZE = 1500

        self.message_port_register_in(pmt.string_to_symbol("app in"))
        self.message_port_register_in(pmt.string_to_symbol("phy in"))
        self.message_port_register_out(pmt.string_to_symbol("app out"))
        self.message_port_register_out(pmt.string_to_symbol("phy out"))

        self.set_msg_handler(pmt.string_to_symbol("app in"), self.app_in)
        self.set_msg_handler(pmt.string_to_symbol("phy in"), self.phy_in)

    def app_in(self, msg):
        print(type(msg))
        if pmt.is_pair(msg):
            str_msg = pmt.to_python(pmt.cdr(msg))
            print(str_msg)
            msg_len = len(str_msg)
            print(msg_len)

        try:
            if msg_len > self.MAX_PAYLOAD_SIZE:
                raise ValueError('Frame too large (> 1500)')
        except Exception as exp:
            print('Frame too large (> 1500)')
            return
            pass

        self.generate_mac_data_frame(str_msg)

        # 
        # mac_dict = dict()
        # mac = pmt.make_blob()
        self.message_port_pub(pmt.mp("phy out"), pmt.cons(mac_dict, mac))

    def generate_mac_data_frame(self, msdu):
        print("msdu")
        for x in msdu:
            print(x)
            pass
        
        pass

    def phy_in(self, msg):
        print('function phy_in')
        pass


    def work(self, input_items, output_items):
        return False

