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

class redis_source(gr.sync_block):
    """
    docstring for block redis_source
    """
    def __init__(self, db_ch, db_port, db_host, db_idx):
        gr.sync_block.__init__(self,
            name="redis_source",
            in_sig=None,
            out_sig=None)

        self.db_ch = db_ch
        self.db_port = db_port
        self.db_host = db_host
        self.db_idx = db_idx
        self.msg = ""
        self.subprefix = f'__keyspace@{self.db_idx}__'

        # Connect to database
        self.redis_db = redis.Redis(host=self.db_host, port=self.db_port, db=self.db_idx)
        # set notify config
        if self.redis_db.config_get('notify-keyspace-events') != "KEA":
            self.redis_db.config_set('notify-keyspace-events', 'KEA')

        self.message_port_register_out(pmt.string_to_symbol("pdu"))
        self.thread = threading.Thread(target=self.run_subscribe)

    def start(self):
        self.thread.start()
        return True

    def stop(self):
        self.thread.join()
        if self.redis_thread:
            self.redis_thread.stop()
        return True

    def run_subscribe(self):
        self.pubsub = self.redis_db.pubsub()
        # TODO: change listening channel depends on input setting.
        self.pubsub.psubscribe(**{self.subprefix+":Trans:*": self.event_handler})
        self.redis_thread = self.pubsub.run_in_thread(sleep_time=0.01)

    def event_handler(self, msg):
        self.msg = ""
        try:
            key = msg["channel"].decode("utf-8")
            split_key = key.split(":")
            db_key = ":".join([i for i in split_key[1:]])
            if db_key:
                self.msg = self.redis_db.get(db_key).decode("utf-8")
                self.message_port_pub(pmt.string_to_symbol("pdu"), pmt.intern(self.msg))
        except Exception as exp:
            return

    def work(self, input_items, output_items):
        return False

