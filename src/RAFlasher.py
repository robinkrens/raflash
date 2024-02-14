import os
import math
import time
import argparse
import tempfile
from tqdm import tqdm
from RAConnect import *
from RAPacker import *

SECTOR_SIZE = 2048

def int_to_hex_list(num):
    hex_string = hex(num)[2:].upper()  # convert to hex string
    hex_string = hex_string.zfill(8) # pad for 8 char's long
    hex_list = [f'0x{hex_string[c:c+2]}' for c in range(0, 8, 2)]
    return hex_list

def hex_type(string):
    try:
        value = int(string, 16)
        return value
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{string}' is not a valid hexadecimal value.")

def set_size_boundaries(start_addr, size):
    if start_addr % SECTOR_SIZE:
        raise ValueError(f"start addr not aligned on sector size {SECTOR_SIZE}")

    if size < SECTOR_SIZE:
        print("Warning: you are trying to write something that is less than one sector size: padding with zeroes")

    blocks = (size + SECTOR_SIZE - 1) // SECTOR_SIZE
    end_addr = blocks * SECTOR_SIZE + start_addr - 1

    if (end_addr <= start_addr):
        raise ValueError(f"End address smaller or equal than start_address")

    if (end_addr > 0x3FFFF):
        raise ValueError(f"Binary file is bigger than available ROM space")

    return (start_addr, end_addr)

def inquire_connection(dev):
    packed = pack_pkt(INQ_CMD, "")
    dev.send_data(packed)
    info = dev.recv_data(7)
    if info == bytearray(b'\x00') or info == bytearray(b''):
        return False
    msg = unpack_pkt(info)
    #print("Connection already established")
    return True

def get_area_info(dev):
    for i in [0,1,2]:
        packed = pack_pkt(ARE_CMD, [str(i)])
        dev.send_data(packed)
        info = dev.recv_data(23)
        msg = unpack_pkt(info)
        fmt = '>BIIII'
        KOA, SAD, EAD, EAU, WAU = struct.unpack(fmt, bytes(int(x, 16) for x in msg))
        print(f'Area {KOA}: {hex(SAD)}:{hex(EAD)} (erase {hex(EAU)} - write {hex(WAU)})')

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
        rint('Unknown MCU type')
    print(f'Serial interface speed: {SCI} Hz')
    print(f'Recommend max UART baud rate: {RMB} bps')
    print(f'User area in Code flash [{NOA & 0x1}|{NOA & 0x02 >> 1}]')
    print(f'User area in Data flash [{NOA & 0x03 >> 2}]')
    print(f'Config area [{NOA & 0x04 >> 3}]')
    print(f'Boot firmware: version {BFV >> 8}.{BFV & 0xFF}')

def erase_chip(dev, start_addr, size):
    
    if size == None:
        size = 0x3FFFF - start_addr # erase all
    
    (start_addr, end_addr) = set_size_boundaries(start_addr, size)
    print(f'Erasing {hex(start_addr)}:{hex(end_addr)}')

    # setup initial communication
    SAD = int_to_hex_list(start_addr)
    EAD = int_to_hex_list(end_addr)
    packed = pack_pkt(ERA_CMD, SAD + EAD)
    dev.send_data(packed)
    
    ret = dev.recv_data(7, timeout=1000) # erase takes usually a bit longer
    unpack_pkt(ret) 
    print("Erase complete")

def read_img(dev, img, start_addr, size):
    
    if size == None:
        size = 0x3FFFF - start_addr # read maximum possible
    
    (start_addr, end_addr) = set_size_boundaries(start_addr, size)
    print(hex(start_addr), hex(end_addr))

    # setup initial communication
    SAD = int_to_hex_list(start_addr)
    EAD = int_to_hex_list(end_addr)
    packed = pack_pkt(REA_CMD, SAD + EAD)
    dev.send_data(packed)

    # calculate how many packets are have to be received
    nr_packet = (end_addr - start_addr) // 1024 # TODO: set other than just 1024

    with open(img, 'wb') as f:
        for i in tqdm(range(0, nr_packet+1), desc="Reading progress"):
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

    if size == None:
        size = file_size

    if size > file_size:
        raise ValueError("Write size > file size")

    (start_addr, end_addr) = set_size_boundaries(start_addr, size)
    print(start_addr, end_addr)
    
    chunk_size = 1024 # max is 1024 according to protocol

    # setup initial communication
    SAD = int_to_hex_list(start_addr)
    EAD = int_to_hex_list(end_addr)
    packed = pack_pkt(WRI_CMD, SAD + EAD)
    dev.send_data(packed)
    ret = dev.recv_data(7)
    unpack_pkt(ret) 

    with open(img, 'rb') as f:
        with tqdm(total=file_size, desc="Writing progress") as pbar:
            chunk = f.read(chunk_size)
            pbar.update(len(chunk))
            while chunk:
                if len(chunk) != chunk_size:
                    padding_length = chunk_size - len(chunk)
                    chunk += b'\0' * padding_length
                packed = pack_pkt(WRI_CMD, chunk, ack=True)
                dev.send_data(packed)
                reply_len = 7
                reply = dev.recv_data(reply_len)
                msg = unpack_pkt(reply)
                chunk = f.read(chunk_size)
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

    # Subparser for the write command
    write_parser = subparsers.add_parser("write", help="Write data to flash")
    write_parser.add_argument("--start_address", type=hex_type, default='0x0000', help="Start address")
    write_parser.add_argument("--size", type=hex_type, default=None, help="Size in bytes")
    write_parser.add_argument("--verify", action="store_true", help="Verify after writing")
    write_parser.add_argument("file_name", type=str, help="File name")

    # Subparser for the read command
    read_parser = subparsers.add_parser("read", help="Read data from flash")
    read_parser.add_argument("--start_address", type=hex_type, default='0x0000', help="Start address")
    read_parser.add_argument("--size", type=hex_type, default=None, help="Size in bytes")
    read_parser.add_argument("file_name", type=str, help="File name")

    erase_parser = subparsers.add_parser("erase", help="Erase sectors")
    erase_parser.add_argument("--start_address", default='0x0000', type=hex_type, help="Start address")
    erase_parser.add_argument("--size", type=hex_type, help="Size")

    # Subparser for the info command
    subparsers.add_parser("info", help="Show flasher information")

    args = parser.parse_args()

    if args.command == "write":
        dev = RAConnect(vendor_id=0x045B, product_id=0x0261)
        status_con = inquire_connection(dev)
        if not status_con:
            dev.confirm_connection()
        #print(args.start_address, args.size)
        write_img(dev, args.file_name, args.start_address, args.size, args.verify)
    elif args.command == "read":
        dev = RAConnect(vendor_id=0x045B, product_id=0x0261)
        status_con = inquire_connection(dev)
        if not status_con:
            dev.confirm_connection()
        read_img(dev, args.file_name, args.start_address, args.size)
    elif args.command == "erase":
        dev = RAConnect(vendor_id=0x045B, product_id=0x0261)
        status_con = inquire_connection(dev)
        if not status_con:
            dev.confirm_connection()
        erase_chip(dev, args.start_address, args.size)
    elif args.command == "info":
        dev = RAConnect(vendor_id=0x045B, product_id=0x0261)
        status_con = inquire_connection(dev)
        if not status_con:
            dev.confirm_connection()
        get_dev_info(dev)
        get_area_info(dev)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
    
