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
import numpy

import pmt
from gnuradio import gr

class redis_subscriber(gr.sync_block):
    """
    docstring for block redis_subscriber
    """
    def __init__(self, db_ch, db_port, db_host, db_idx):
        gr.sync_block.__init__(self,
            name="redis_subscriber",
            in_sig=None,
            out_sig=None)

        self.db_ch = db_ch
        self.db_port = db_port
        self.db_host = db_host
        self.db_idx = db_idx
        self.msg = ""

        # Connect to database
        self.redis_db = redis.Redis(host=self.db_host, port=self.db_port, db=self.db_idx)
        # set notify config
        # if self.redis_db.config_get('notify-keyspace-events') != "KEA":
        #     self.redis_db.config_set('notify-keyspace-events', 'KEA')

        # self.pubsub = self.redis_db.pubsub()
        # # TODO: change listening channel depends on input setting.
        # print("psubscribe...")
        # self.pubsub.psubscribe(**{'__keyevent@0__:*': self.event_handler})
        # # self.pubsub.run_in_thread(sleep_time=0.01)

        print("set_msg_handler...")
        self.message_port_register_in(pmt.string_to_symbol("trigger"))
        self.message_port_register_out(pmt.string_to_symbol("pdu"))
        self.set_msg_handler(pmt.intern('trigger'), self.handle_msg)

    def handle_msg(self, trigger):
        # self.msg = self.redis_db.get("valKey:test")
        print("self.msg: ", self.msg, end=' ')
        try:
            if self.msg != "":
                print(' is string, show to message debug')
                self.message_port_pub(pmt.string_to_symbol('pdu'), pmt.intern(self.msg))
            else:
                print(' is empty string, do not show to message debug')
        except Exception as exp:
            pass
        pass

    def event_handler(self, msg):
        print("Catching some event...")
        self.msg = ""
        try: 
            key = msg["data"].decode("utf-8")
            if key:
                value = self.redis_db.get(key)
                self.msg = value
        except Exception as exp:
            pass

    def work(self, input_items, output_items):
        return False

