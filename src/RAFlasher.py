import os
import math
from RAConnect import *
from RAPacker import *

SECTOR_SIZE = 2048

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


dev = RAConnect(vendor_id=0x1a86, product_id=0x7523)
write_img(dev, 'src/sample.bin', 0x800, None, True)
    
