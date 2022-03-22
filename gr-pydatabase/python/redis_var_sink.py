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
import threading

import numpy
from gnuradio import gr

class redis_var_sink(gr.sync_block):
    """
    docstring for block redis_var_sink
    """
    def __init__(self,  db_ch, db_port, db_host, db_idx):
        gr.sync_block.__init__(self,
            name="redis_var_sink",
            in_sig=[numpy.float32],
            out_sig=None)

        self.db_ch = db_ch
        self.db_port = db_port
        self.db_host = db_host
        self.db_idx = db_idx
        self.redis_db = redis.Redis(host=self.db_host, port=self.db_port, db=self.db_idx)

        self.value = 0.0
        print(f'Set self.value: {self.value}')

        self.message_port_register_in(pmt.string_to_symbol("var in"))
        self.set_msg_handler(pmt.string_to_symbol("var in"), self.monitor_input)

    def monitor_input(self, var_in):
        if self.value != var_in:
            print(f'input change! from {self.value} to {var_in}')
            self.value = var_in


    def work(self, input_items, output_items):
        in0 = input_items[0]
        # <+signal processing here+>
        return len(input_items[0])

