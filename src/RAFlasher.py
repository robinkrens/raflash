import os
import math
import argparse
from RAConnect import *
from RAPacker import *

SECTOR_SIZE = 2048

def int_to_hex_list(num):
    hex_string = hex(num)[2:].upper()  # convert to hex string
    hex_string = hex_string.zfill(8) # pad for 8 char's long
    hex_list = [f'0x{hex_string[c:c+2]}' for c in range(0, 8, 2)]
    return hex_list

def get_dev_info(dev):

    packed = pack_pkt(SIG_CMD, "")
    dev.send_data(packed)
    #info_ret = dev.recv_data(17)
    info = b'\x81\x00\x0D\x3A\x01\x31\x2d\x00\x00\x1e\x84\x80\x04\x02\x0a\x08' # test
    fmt = '>IIIBBH'
    _HEADER, SCI, RMB, NOA, TYP, BFV = struct.unpack(fmt, info)
    print(f'Ver{BFV >> 8}.{BFV & 0xFF}')

def verify_img(dev, img, start_addr, end_addr):
    raise Exception("Not implemented")

def write_img(dev, img, start_addr, end_addr, verify=False):

    if os.path.exists(img):
        file_size = os.path.getsize(img)
    else:
        raise Exception(f'file {img} does not exist')

    # calculate / check start and end address 
    if start_addr == None or end_addr == None:
        if start_addr == None:
            start_addr = 0
        # align start addr
        if start_addr % SECTOR_SIZE:
            raise ValueError(f"start addr not aligned on sector size {SECTOR_SIZE}")
        blocks = (file_size + SECTOR_SIZE - 1) // SECTOR_SIZE
        end_addr = blocks * SECTOR_SIZE + start_addr
        print(end_addr)
    
    chunk_size = 64 # max is 1024
    if (start_addr > 0xFF800): # for RA4 series
        raise ValueError("start address value error")
    if (end_addr <= start_addr or end_addr > 0xFF800):
        raise ValueError("end address value error")

    # setup initial communication
    SAD = int_to_hex_list(start_addr)
    EAD = int_to_hex_list(end_addr)
    packed = pack_pkt(WRI_CMD, SAD + EAD)
    dev.send_data(packed)
    ret = dev.recv_data(7)

    with open(img, 'rb') as f:
        chunk = f.read(chunk_size)
        while chunk:
            packed = pack_pkt(WRI_CMD, chunk)
            print(f'Sending {len(chunk)} bytes')
            dev.send_data(packed)
            reply_len = 7
            reply = dev.recv_data(reply_len)
            #reply = b'\x81\x00\x02\x00\x00\xFE\x03' # test reply
            if not reply == False:
                msg = unpack_pkt(reply)
                print(msg)
            chunk = f.read(chunk_size)

def main():
    parser = argparse.ArgumentParser(description="RA Flasher Tool")

    subparsers = parser.add_subparsers(dest="command", title="Commands")

    # Subparser for the write command
    write_parser = subparsers.add_parser("write", help="Write data to flash")
    write_parser.add_argument("--start_address", type=int, default=0x0000, help="Start address")
    write_parser.add_argument("--end_address", type=int, help="End address")
    write_parser.add_argument("--verify", action="store_true", help="Verify after writing")
    write_parser.add_argument("file_name", type=str, help="File name")

    # Subparser for the read command
    read_parser = subparsers.add_parser("read", help="Read data from flash")
    read_parser.add_argument("--start_address", type=int, default=0x000, help="Start address")
    read_parser.add_argument("--size", type=int, default=1024, help="Size in bytes")
    read_parser.add_argument("file_name", type=str, help="File name")

    # Subparser for the info command
    subparsers.add_parser("info", help="Show flasher information")

    args = parser.parse_args()

    if args.command == "write":
        dev = RAConnect(vendor_id=0x1a86, product_id=0x7523)
        print(args)
        write_img(dev, args.file_name, args.start_address, args.end_address, args.verify)
    elif args.command == "read":
        print('read command')
    elif args.command == "info":
        dev = RAConnect(vendor_id=0x1a86, product_id=0x7523)
        get_dev_info(dev)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
    
