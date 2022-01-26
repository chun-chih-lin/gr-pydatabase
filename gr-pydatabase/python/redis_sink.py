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

import numpy
from gnuradio import gr

class redis_sink(gr.sync_block):
    """
    docstring for block redis_sink
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
        # Check if pdu is PDU
        print("Check if pdu is PDU...")
        if pmt.is_pair(pdu):
            print("It is a PDU!")
            meta = pmt.to_python(pmt.car(pdu))
            if meta is None:
                meta = dict()

            # print("meta: \n", meta)

            vector = pmt.cdr(pdu)
            payload = ""
            if pmt.is_u8vector(vector):
                vector = pmt.u8vector_elements(vector)
                payload = "".join([chr(r) for r in vector[24:]])
                self.set_to_db(payload)
        pass

    def set_to_db(self, payload):
        print("Parsing the payload and set the information to db...")
        print("payload: ", payload)
        pass

    def work(self, input_items, output_items):
        return False

