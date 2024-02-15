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
import usb.core
import usb.util
from src.RAPacker import *

MAX_TRANSFER_SIZE = 2048 + 6 # include header and footer

class RAConnect:
    def __init__(self, vendor_id, product_id):
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.ep_in = 0x81
        self.ep_out = 0x02
        self.max_tries = 20
        self.timeout_ms = 100
        self.dev = None
        self.rx_ep = None
        self.tx_ep = None
        self.chip_layout = []
        self.sel_area = 0 # default to Area 0

        self.find_device()
        status_conn = self.inquire_connection()
        if not status_conn:
            self.confirm_connection()

    def find_device(self):
        self.dev = usb.core.find(idVendor=self.vendor_id, idProduct=self.product_id)
        if self.dev is None:
            raise ValueError(f"Device {self.vendor_id}:{self.product_id} not found\nAre you sure it is connected?")

        for config in self.dev:
            intf = config[(1,0)]
            product_name = usb.util.get_string(self.dev, self.dev.iProduct)
            print(f'Found {product_name} ({self.vendor_id}:{self.product_id})')
            if self.dev.is_kernel_driver_active(intf.bInterfaceNumber):
                print("Found kernel driver, detaching ... ")
                self.dev.detach_kernel_driver(intf.bInterfaceNumber)
            for ep in intf:
                if (ep.bmAttributes == 0x02):
                    if ep.bEndpointAddress == self.ep_in:
                        self.rx_ep = ep
                    elif ep.bEndpointAddress == self.ep_out:
                        self.tx_ep = ep
            return True

        raise ValueError("Device does not have a CDC interface")


    def inquire_connection(self):
        packed = pack_pkt(INQ_CMD, "")
        self.send_data(packed)
        info = self.recv_data(7)
        if info == bytearray(b'\x00') or info == bytearray(b''):
            return False
        msg = unpack_pkt(info)
        #print("Connection already established")
        return True

    def confirm_connection(self):
        for i in range(self.max_tries):
            try:
                self.tx_ep.write(bytes([0x55]), self.timeout_ms)
                ret = self.rx_ep.read(1, self.timeout_ms)
                if ret[0] == 0xC3:
                    print("Reply received (0xC3)")
                    return True
            except usb.core.USBError as e:
                print(f"Timeout: retry #{i}", e)
        return False

    def authenticate_connection(self):
        raise Exception("Not implemented")

    def set_chip_layout(self, cfg):
        if cfg == None:
            raise ValueError("Could net get chip layout")
        self.chip_layout = cfg

    def send_data(self, packed_data):
        if (self.tx_ep == None):
            return False
        try:
            self.tx_ep.write(packed_data, self.timeout_ms)
        except usb.core.USBError as e:
            print(f"Timeout: error", e)
            return False
        return True

    def recv_data(self, exp_len, timeout=100):
        msg = bytearray(b'')
        if (exp_len > MAX_TRANSFER_SIZE):
            raise ValueError(f"length package {exp_len} over max transfer size")
        if (self.rx_ep == None):
            return False
        try:
            received = 0
            while received != exp_len:
                buf = self.rx_ep.read(exp_len, timeout)
                msg += buf
                received += len(buf)
                if received == exp_len:
                    return msg
        except usb.core.USBError as e:
            print(f"Timeout: error", e)
        return msg
