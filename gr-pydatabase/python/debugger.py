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
import time
from gnuradio import gr

class debugger(gr.sync_block):
    """
    docstring for block debugger
    """
    def __init__(self):
        gr.sync_block.__init__(self,
            name="debugger",
            in_sig=None,
            out_sig=None)

        self.message_port_register_in(pmt.string_to_symbol("pdu"))
        self.set_msg_handler(pmt.string_to_symbol("pdu"), self.process_pdu)

    def p(self, msg):
        print(f"[Debugger] {msg}")

    def process_pdu(self, pdu):
        time.sleep(0.1)
        if pmt.is_pair(pdu):
            msdu = pmt.to_python(pmt.car(pdu))
            pdu_cdr = pmt.to_python(pmt.cdr(pdu))
            print(f"msdu: {msdu}")
            print("it is a pair")
            print(f"pdu_cdr: {pdu_cdr} {type(pdu_cdr)} {len(pdu_cdr)} ele: {pdu_cdr[0]}, {type(pdu_cdr[0])}")

        elif pmt.is_symbol(pdu):
            self.p(f"It's a symbol. {pdu}")

        else:
            self.p("Error, not a valid type")
            return


    def work(self, input_items, output_items):
        return False

