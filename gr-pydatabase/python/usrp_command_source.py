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

import pmt
import threading
import time
import redis

import numpy
from gnuradio import gr

class usrp_command_source(gr.sync_block):
    def __init__(self):
        gr.sync_block.__init__(self,
            name="usrp_command_source",
            in_sig=None,
            out_sig=None)
        self.db_host = 'localhost'
        self.db_port = 6379
        self.db_idx = 0
        self.subprefix = f'__keyspace@{self.db_idx}__'

        self.db = redis.Redis(host=self.db_host, port=self.db_port, db=self.db_idx)
        self.db.config_set('notify-keyspace-events', 'KEA')

        self.pipt = self.db.pipeline()
        self.tune_rf = pmt.make_dict()
        self.message_port_register_out(pmt.intern("msg"))
        self.thread = threading.Thread(target=self.run)

    def start(self):
        self.thread.start()
        return True

    def stop(self):
        self.thread.join()
        if self.redis_thread:
            self.redis_thread.stop()
        return True

    def run(self):
        self.pubsub = self.db.pubsub()
        self.pubsub.psubscribe(**{f'{self.subprefix}:TuneRF:*': self.event_handler})
        self.redis_thread = self.pubsub.run_in_thread(sleep_time=0.01)
    """
    Action: Hash Set
    Key: TuneRF:11
    Values:
        Freq: int in Hz. e.g., 2412000000
        Gain: nomalized gain. e.g., 0.1
    """
    def event_handler(self, msg):
        self.msg = ""
        try:
            key = msg["channel"].decode("utf-8")
            split_key = key.split(":")
            db_key = ":".join([i for i in split_key[1:]])
            if db_key:
                hset = self.db.hgetall("TuneRF:11")
                tune_list = list(hset.values())
                self.tune_rf = pmt.dict_add(self.tune_rf, pmt.to_pmt('chan'), pmt.to_pmt(0))
                self.tune_rf = pmt.dict_add(self.tune_rf, pmt.to_pmt('freq'), pmt.to_pmt(float(tune_list[0])))
                #self.tune_rf = pmt.dict_add(self.tune_rf, pmt.to_pmt('gain'), pmt.to_pmt(float(tune_list[1])))
                self.message_port_pub(pmt.intern("msg"), self.tune_rf)
                self.tune_rf = pmt.make_dict()
                #print(f"Setting to new frequency: {tune_list[0]} with gain: {tune_list[1]}, {time.time()}")
        except Exception as exp:
            print(f"[Tuning RF] Exception: {exp}")
            return

    def work(self, input_items, output_items):
        return False

