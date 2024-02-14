import os
import math
import time
import argparse
from tqdm import tqdm
from RAConnect import *
from RAPacker import *

SECTOR_SIZE = 2048

def int_to_hex_list(num):
    hex_string = hex(num)[2:].upper()  # convert to hex string
    hex_string = hex_string.zfill(8) # pad for 8 char's long
    hex_list = [f'0x{hex_string[c:c+2]}' for c in range(0, 8, 2)]
    return hex_list

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
        print("===================")
        packed = pack_pkt(ARE_CMD, [str(i)])
        dev.send_data(packed)
        info = dev.recv_data(23)
        msg = unpack_pkt(info)
        fmt = '>BIIII'
        KOA, SAD, EAD, EAU, WAU = struct.unpack(fmt, bytes(int(x, 16) for x in msg))
        print(f'Area {KOA} - {hex(SAD)}:{hex(EAD)}')
        print(f'Erase {hex(EAU)} bytes - write {hex(WAU)} bytes')

def get_dev_info(dev):

    packed = pack_pkt(SIG_CMD, "")
    dev.send_data(packed)
    info = dev.recv_data(18)
    fmt = '>IIIBBHH'
    _HEADER, SCI, RMB, NOA, TYP, BFV, _FOOTER = struct.unpack(fmt, info)
    print('Chip info:')
    print('====================')
    print(f'Serial interface speed: {SCI} Hz')
    print(f'Recommend max UART baud rate {RMB} bps')
    print(f'User area in Code flash [{NOA & 0x1}|{NOA & 0x02 >> 1}]')
    print(f'User area in Data flash [{NOA & 0x03 >> 2}]')
    print(f'Config area [{NOA & 0x04 >> 3}]')
    if TYP == 0x02:
        print('RA MCU + RA2/RA4 Series')
    elif TYP == 0x03:
        print('RA MCU + RA6 Series')
    else:
        print('Unknown MCU type')
    print(f'Boot firmware version {BFV >> 8}.{BFV & 0xFF}')
    print('====================')


def verify_img(dev, img, start_addr, end_addr):
    raise Exception("Not implemented")

def read_img(dev, img, start_addr, end_addr):
    
    # calculate / check start and end address 
    if start_addr == None or end_addr == None:
        if start_addr == None:
            start_addr = 0
        # align start addr
        if start_addr % SECTOR_SIZE:
            raise ValueError(f"start addr not aligned on sector size {SECTOR_SIZE}")
        blocks = (file_size + SECTOR_SIZE - 1) // SECTOR_SIZE
        end_addr = blocks * SECTOR_SIZE + start_addr
    
    if (start_addr > 0xFF800): # for RA4 series
        raise ValueError("start address value error")
    if (end_addr <= start_addr or end_addr > 0xFF800):
        raise ValueError("end address value error")
    
    # setup initial communication
    SAD = int_to_hex_list(start_addr)
    EAD = int_to_hex_list(end_addr)
    packed = pack_pkt(REA_CMD, SAD + EAD)
    dev.send_data(packed)

    # calculate how many packets are have to be received
    nr_packet = (end_addr - start_addr) // 1024 # TODO: set other than just 1024

    with open('output.bin', 'wb') as f:
        for i in tqdm(range(0, nr_packet+1), desc="Reading progess"):
            ret = dev.recv_data(1024 + 6)
            chunk = unpack_pkt(ret)
            chunky = bytes(int(x, 16) for x in chunk)
            f.write(chunky)
            packed = pack_pkt(REA_CMD, ['0x00'], ack=True)
            dev.send_data(packed)


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
        end_addr = blocks * SECTOR_SIZE + start_addr - 1
    
    chunk_size = 1024 # max is 1024
    #if (start_addr > 0xFF800): # for RA4 series
    #    raise ValueError("start address value error")
    #if (end_addr <= start_addr or end_addr > 0xFF800):
    #    raise ValueError("end address value error")

    # setup initial communication
    SAD = int_to_hex_list(start_addr)
    EAD = int_to_hex_list(end_addr)
    #packed = pack_pkt(ERA_CMD, SAD + EAD) # actually works
    packed = pack_pkt(WRI_CMD, SAD + EAD)
    dev.send_data(packed)
    ret = dev.recv_data(7)
    unpack_pkt(ret) 

    with open(img, 'rb') as f:
        with tqdm(total=file_size, desc="Sending chunks") as pbar:
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
        dev = RAConnect(vendor_id=0x045B, product_id=0x0261)
        status_con = inquire_connection(dev)
        if not status_con:
            dev.confirm_connection()
        write_img(dev, "src/sample.bin", 0x8000, None)
    elif args.command == "read":
        dev = RAConnect(vendor_id=0x045B, product_id=0x0261)
        status_con = inquire_connection(dev)
        if not status_con:
            dev.confirm_connection()
        read_img(dev, "save.bin", 0x0000, 0x3FFFF)
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
    
