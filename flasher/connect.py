# Copyright (C) - Robin Krens - 2024
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
import serial
import serial.threaded
import time
import usb.core
import usb.util

LOW_PULSE = 0x00
ACK = 0x00
GENERIC_CODE = 0x55
BOOT_CODE = 0xC3

VENDOR_ID = 0x045B
PRODUCT_ID = 0x0261

EP_IN = 0x82
EP_OUT = 0x02

MAX_TRIES = 20

def find_device(vendor_id, product_id):
    dev = usb.core.find(idVendor=vendor_id, idProduct=product_id)
    if dev is None:
        raise ValueError(f"Device {vendor_id}:{product_id} not found\n Are you sure it is connected?")

    for config in dev:
        for intf in config:
            if usb.util.find_descriptor(config, custom_match=lambda d: (d.bInterfaceClass == 0x02 or d.bInterfaceClass == 0xFF)):
                print(f"Found serial device with 0x02 | 0xFF")
                TxD, RxD = None, None
                if dev.is_kernel_driver_active(intf.bInterfaceNumber):
                    print(f"Found kernel driver, detaching ... ")
                    dev.detach_kernel_driver(intf.bInterfaceNumber)
                for ep in intf:
                    if (ep.bmAttributes == 0x02):
                        if ep.bEndpointAddress == EP_IN:
                            RxD = ep
                            print(ep)
                        elif ep.bEndpointAddress == EP_OUT:
                            TxD = ep
                            print(ep)
                return (dev, RxD, TxD)

    raise ValueError("Device does not have a serial interface")

def establish_connection():
    dev, rx_ep, tx_ep = find_device(0x1a86, 0x7523)
    ret = []
    for i in range(MAX_TRIES):
        try:
            tx_ep.write(b'\x00', 100)
            ret = rx_ep.read(1, 100)
            if a[0] == ACK:
                print("ACK received")
                return True
        except:
            print(f"Timeout: retry #", i)
    return False

def confirm_connection():
    dev, rx_ep, tx_ep = find_device(0x1a86, 0x7523)
    ret = []
    for i in range(MAX_TRIES):
        try:
            tx_ep.write(b'\x55', 100)
            ret = rx_ep.read(1, 100)
            if a[0] == BOOT_CODE:
                print("ACK received")
                return True
        except:
            print(f"Timeout: retry #", i)
    return False

if not establish_connection():
    print("Cannot connect")
    sys.exit(0)

if not confirm_connection():
    print("Failed to confirm boot code")
    sys.exit(0)
