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

import os
import math
import time
import argparse
import tempfile
from tqdm import tqdm
from raflash.RAConnect import *
from raflash.RAPacker import *

VENDOR_ID = 0x045B
PRODUCT_ID = 0x0261

commands = {
    "write": lambda dev, args: write_img(dev, args.file_name, args.start_address, args.size, args.verify),
    "read": lambda dev, args: read_img(dev, args.file_name, args.start_address, args.size),
    "erase": lambda dev, args: erase_chip(dev, args.start_address, args.size),
    "info": lambda dev, args: (get_dev_info(dev), dev.set_chip_layout(get_area_info(dev, output=True)))
}

def int_to_hex_list(num):
    hex_string = hex(num)[2:].upper() # convert to hex string
    hex_string = hex_string.zfill(8) # pad for 8 char's long
    hex_list = [f'0x{hex_string[c:c+2]}' for c in range(0, 8, 2)]
    return hex_list

def hex_type(string):
    try:
        value = int(string, 16)
        return value
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{string}' is not a valid hexadecimal value.")

def set_size_boundaries(dev, start_addr, size):

    sector_size = dev.chip_layout[dev.sel_area]['ALIGN']  # currently only area 0 supported

    if start_addr % sector_size:
        raise ValueError(f"start addr not aligned on sector size {sector_size}")

    if size < sector_size:
        print("Warning: you are trying to write something that is less than one sector size: padding with zeroes")

    blocks = (size + sector_size - 1) // sector_size
    end_addr = blocks * sector_size + start_addr - 1

    if (end_addr <= start_addr):
        raise ValueError("End address smaller or equal than start_address")

    if (end_addr > dev.chip_layout[dev.sel_area]['EAD']):
        raise ValueError("Binary file is bigger than available ROM space")

    return (start_addr, end_addr)

def get_area_info(dev, output=False):
    cfg = {}
    for i in [0, 1, 2]:
        packed = pack_pkt(ARE_CMD, [str(i)])
        dev.send_data(packed)
        info = dev.recv_data(23)
        msg = unpack_pkt(info)
        fmt = '>BIIII'
        KOA, SAD, EAD, EAU, WAU = struct.unpack(fmt, bytes(int(x, 16) for x in msg))
        cfg[i] = {"SAD": SAD, "EAD": EAD, "ALIGN": EAU}
        if output:
            print(f'Area {KOA}: {hex(SAD)}:{hex(EAD)} (erase {hex(EAU)} - write {hex(WAU)})') 
    return cfg

def get_dev_info(dev):
    packed = pack_pkt(SIG_CMD, "")
    dev.send_data(packed)
    info = dev.recv_data(18)
    fmt = '>IIIBBHH'
    _HEADER, SCI, RMB, NOA, TYP, BFV, _FOOTER = struct.unpack(fmt, info)
    print('====================')
    if TYP == 0x02:
        print('Chip: RA MCU + RA2/RA4 Series')
    elif TYP == 0x03:
        print('Chip: RA MCU + RA6 Series')
    else:
        print('Unknown MCU type')
    print(f'Serial interface speed: {SCI} Hz')
    print(f'Recommend max UART baud rate: {RMB} bps')
    print(f'User area in Code flash [{NOA & 0x1}|{NOA & 0x02 >> 1}]')
    print(f'User area in Data flash [{NOA & 0x03 >> 2}]')
    print(f'Config area [{NOA & 0x04 >> 3}]')
    print(f'Boot firmware: version {BFV >> 8}.{BFV & 0xFF}')

def erase_chip(dev, start_addr, size):
    if size is None:
        size = dev.chip_layout[dev.sel_area]['EAD'] - start_addr  # erase all
    
    (start_addr, end_addr) = set_size_boundaries(dev, start_addr, size)
    print(f'Erasing {hex(start_addr)}:{hex(end_addr)}')

    # setup initial communication
    SAD = int_to_hex_list(start_addr)
    EAD = int_to_hex_list(end_addr)
    packed = pack_pkt(ERA_CMD, SAD + EAD)
    dev.send_data(packed)
    
    ret = dev.recv_data(7, timeout=1000)  # erase takes usually a bit longer
    unpack_pkt(ret) 
    print("Erase complete")

def read_img(dev, img, start_addr, size):
    
    if size is None:
        size = 0x3FFFF - start_addr  # read maximum possible
    
    (start_addr, end_addr) = set_size_boundaries(dev, start_addr, size)

    # setup initial communication
    SAD = int_to_hex_list(start_addr)
    EAD = int_to_hex_list(end_addr)
    packed = pack_pkt(REA_CMD, SAD + EAD)
    dev.send_data(packed)

    # calculate how many packets are have to be received
    nr_packet = (end_addr - start_addr) // 1024  # TODO: set other than just 1024

    with open(img, 'wb') as f:
        for i in tqdm(range(0, nr_packet + 1), desc="Reading progress"):
            ret = dev.recv_data(1024 + 6)
            chunk = unpack_pkt(ret)
            chunky = bytes(int(x, 16) for x in chunk)
            f.write(chunky)
            packed = pack_pkt(REA_CMD, ['0x00'], ack=True)
            dev.send_data(packed)


def write_img(dev, img, start_addr, size, verify=False):

    if os.path.exists(img):
        file_size = os.path.getsize(img)
    else:
        raise Exception(f'file {img} does not exist')

    if size is None:
        size = file_size

    if size > file_size:
        raise ValueError("Write size > file size")

    (start_addr, end_addr) = set_size_boundaries(dev, start_addr, size)

    chunk_size = 1024  # max is 1024 according to protocol

    # setup initial communication
    SAD = int_to_hex_list(start_addr)
    EAD = int_to_hex_list(end_addr)
    packed = pack_pkt(WRI_CMD, SAD + EAD)
    dev.send_data(packed)
    ret = dev.recv_data(7)
    unpack_pkt(ret) 

    totalread = 0
    with open(img, 'rb') as f:
        with tqdm(total=size, desc="Writing progress") as pbar:
            chunk = f.read(chunk_size)
            pbar.update(len(chunk))
            while chunk and totalread < size:
                if len(chunk) != chunk_size:
                    padding_length = chunk_size - len(chunk)
                    chunk += b'\0' * padding_length
                packed = pack_pkt(WRI_CMD, chunk, ack=True)
                dev.send_data(packed)
                reply_len = 7
                reply = dev.recv_data(reply_len)
                msg = unpack_pkt(reply)
                chunk = f.read(chunk_size)
                totalread += chunk_size
                pbar.update(len(chunk))
 
    if verify:
        with tempfile.NamedTemporaryFile(prefix='.hidden_', delete=False) as tmp_file, open(img, 'rb') as cmp_file:
            read_img(dev, tmp_file.name, start_addr, size)
            c1 = tmp_file.read(file_size) # due to byte alignment read file is longer
            c2 = cmp_file.read()
            if c1 == c2:
                print("Verify complete")
            else: 
                print("Verify failed")

def main():
    parser = argparse.ArgumentParser(description="RA Flasher Tool")

    subparsers = parser.add_subparsers(dest="command", title="Commands")

    write_parser = subparsers.add_parser("write", help="Write data to flash")
    write_parser.add_argument("--start_address", type=hex_type, default='0x0000', help="Start address")
    write_parser.add_argument("--size", type=hex_type, default=None, help="Size in bytes")
    write_parser.add_argument("--verify", action="store_true", help="Verify after writing")
    write_parser.add_argument("file_name", type=str, help="File name")

    read_parser = subparsers.add_parser("read", help="Read data from flash")
    read_parser.add_argument("--start_address", type=hex_type, default='0x0000', help="Start address")
    read_parser.add_argument("--size", type=hex_type, default=None, help="Size in bytes")
    read_parser.add_argument("file_name", type=str, help="File name")

    erase_parser = subparsers.add_parser("erase", help="Erase sectors")
    erase_parser.add_argument("--start_address", default='0x0000', type=hex_type, help="Start address")
    erase_parser.add_argument("--size", type=hex_type, help="Size")

    subparsers.add_parser("info", help="Show flasher information")

    args = parser.parse_args()        
    if args.command in commands:
        dev = RAConnect(VENDOR_ID, PRODUCT_ID)
        area_cfg = get_area_info(dev)
        dev.set_chip_layout(area_cfg)
        commands[args.command](dev, args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
