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

class redis_variable(gr.sync_block):
    """
    docstring for block redis_variable
    """
    def __init__(self, db_ch, db_port, db_host, db_idx):
        gr.sync_block.__init__(self,
            name="redis_variable",
            in_sig=None,
            out_sig=[numpy.float32, numpy.float32, numpy.float32])

        self.db_ch = db_ch
        self.db_port = db_port
        self.db_host = db_host
        self.db_idx = db_idx
        self.redis_db = redis.Redis(host=self.db_host, port=self.db_port, db=self.db_idx)

        self.subprefix = f'__keyspace@{self.db_idx}__'

        self.tx_gain = self.get_tx_gain()
        self.rx_gain = self.get_rx_gain()
        self.encoding = self.get_encoding()

        if self.redis_db.config_get('notify-keyspace-events') != "KEA":
            self.redis_db.config_set('notify-keyspace-events', 'KEA')

        self.message_port_register_out(pmt.string_to_symbol("tx_gain"))
        self.message_port_register_out(pmt.string_to_symbol("rx_gain"))
        self.message_port_register_out(pmt.string_to_symbol("encoding"))
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
        self.pubsub.psubscribe(**{self.subprefix+":VAR:*": self.event_handler})
        self.redis_thread = self.pubsub.run_in_thread(sleep_time=0.01)

    def event_handler(self, msg):
        self.msg = ""
        try:
            self.tx_gain = self.get_tx_gain()
            self.rx_gain = self.get_rx_gain()
            self.encoding = self.get_encoding()
            self.message_port_pub(pmt.string_to_symbol("tx_gain"), pmt.intern(self.tx_gain))
            self.message_port_pub(pmt.string_to_symbol("rx_gain"), pmt.intern(self.rx_gain))
            self.message_port_pub(pmt.string_to_symbol("encoding"), pmt.intern(self.encoding))
        except Exception as exp:
            return

    def get_tx_gain(self):
        db_reault = self.redis_db.get('VAR:TXGAIN')
        if db_reault is not None:
            tx_gain = float(db_reault.decode('utf-8'))
            if 0 <= tx_gain <= 1:
                print(f'[get_tx_gain] setting tx_gain: {tx_gain}')
                return tx_gain
            else:
                print(f'[get_tx_gain] {tx_gain} if outside of the range. set to default value...')
        else:
            print(f'[get_tx_gain] No value in db. Set to default value.')
        return 0.75

    def get_rx_gain(self):
        db_reault = self.redis_db.get('VAR:RXGAIN')
        if db_reault is not None:
            rx_gain = float(db_reault.decode('utf-8'))
            if 0 <= rx_gain <= 1:
                print(f'[get_rx_gain] setting rx_gain: {rx_gain}')
                return rx_gain
            else:
                print(f'[get_rx_gain] {rx_gain} if outside of the range. set to default value...')
        else:
            print(f'[get_rx_gain] No value in db. Set to default value.')
        return 0.75

    def get_encoding(self):
        db_reault = self.redis_db.get('VAR:ENCODING')
        if db_reault is not None:
            encoding = float(db_reault.decode('utf-8'))
            if 0 <= encoding <= 7:
                print(f'[get_encoding] setting encoding: {encoding}')
                return encoding
            else:
                print(f'[get_encoding] {encoding} if outside of the range. set to default value...')
        else:
            print(f'[get_encoding] No value in db. Set to default value.')
        return 0


    def work(self, input_items, output_items):
        output_items[0][0] = self.tx_gain
        output_items[0][1] = self.rx_gain
        output_items[0][2] = self.encoding
        return len(output_items[0])
