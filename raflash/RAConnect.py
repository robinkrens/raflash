# Copyright (C) Robin Krens - 2024
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
# 

import sys
import time
import serial
import usb.core
import serial.tools.list_ports
from raflash.RAPacker import *

MAX_TRANSFER_SIZE = 2048 + 6 # include header and footer


class RAConnect:
    def __init__(self, vendor_id, product_id):
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.max_tries = 20
        self.timeout_ms = 100
        self.dev = None
        self.chip_layout = []
        self.sel_area = 0 # default to Area 0

        self.find_device()
        status_conn = self.inquire_connection()
        if not status_conn:
            self.confirm_connection()
    
    def find_port(self):
        ports = serial.tools.list_ports.comports()
        for p in ports:
            if p.vid == self.vendor_id:
                return p.device

        return None

    def find_device(self):
        port = self.find_port()
        try:
            self.dev = serial.Serial(port, 9600)
        except Exception as err:
            raise Exception(f'Failed to open port {err}')

    def inquire_connection(self):
        packed = pack_pkt(INQ_CMD, "")
        self.send_data(packed)
        info = self.recv_data(1)
        if info == bytearray(b'\x00') or info == bytearray(b''):
            return False
        else:
            info += self.recv_data(6)
        msg = unpack_pkt(info)
        # print("Connection already established")
        return True

    def confirm_connection(self):
        for i in range(self.max_tries):
            try:
                self.dev.write(bytes([0x55]))
                ret = self.dev.read(1)
                if ret[0] == 0xC3:
                    print("Reply received (0xC3)")
                    return True
            except Exception as e:
                print(f"Timeout: retry #{i}", e)
        return False

    def authenticate_connection(self):
        raise Exception("Not implemented")

    def set_chip_layout(self, cfg):
        if cfg is None:
            raise ValueError("Could net get chip layout")
        self.chip_layout = cfg

    def send_data(self, packed_data):
        if self.dev is None:
            return False
        try:
            self.dev.write(packed_data)
        except Exception as err:
            print("Timeout: error", err)
            return False
        return True

    def recv_data(self, exp_len, timeout=100):
        msg = bytearray(b'')
        if exp_len > MAX_TRANSFER_SIZE:
            raise ValueError(f"length package {exp_len} over max transfer size")
        if self.dev is None:
            return False
        try:
            received = 0
            while received != exp_len:
                buf = self.dev.read(exp_len)
                msg += buf
                received += len(buf)
                if received == exp_len:
                    return msg
        except Exception as err:
            print("Timeout: error", err)
        return msg
