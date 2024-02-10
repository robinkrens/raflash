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

import struct

# Commands send to boot firmware
INQ_CMD = 0x00
ERA_CMD = 0x12
WRI_CMD = 0x13
REA_CMD = 0x15
IDA_CMD = 0x30
BAU_CMD = 0x34
SIG_CMD = 0x3A
ARE_CMD = 0x3B

# These are combined with send command, for example
# STATUS_OK | ERA_CMD == 0x12
# STATUS_ERR | ERA_CMD = 0x92
STATUS_OK = 0x00
STATUS_ERR = 0x80

# Error codes
ERR_UNSU = 0xC
ERR_PCKT = 0xC1
ERR_CHKS = 0xC2
ERR_FLOW = 0xC3
ERR_ADDR = 0xD0
ERR_BAUD = 0xD4
ERR_PROT = 0xDA
ERR_ID = 0xDB
ERR_SERI = 0xDC
ERR_ERA = 0xE1
ERR_WRI = 0xE2
ERR_SEQ = 0xE7

# used for init sequence
LOW_PULSE = 0x00
GENERIC_CODE = 0x55
BOOT_CODE = 0xC3

TESTID = [
    "0xF0", "0xF1", "0xF2", "0xF3",
    "0xE4", "0xE5", "0xE6", "0xE7",
    "0xD8", "0xD9", "0xDA", "0xDB",
    "0xCC", "0xCD", "0xCE", "0xCF"
]

def calc_sum(cmd, data):
    data_len = len(data)
    lnh = data_len + 1 & 0xFF00
    lnl = data_len + 1 & 0x00FF
    res = lnh + lnl + cmd
    for i in range(data_len):
            if isinstance(data[i], str):
                res += int(data[i], 16)
            else:
                res += ord(data[i])
    res = ~(res - 1) & 0xFF # two's complement
    return (lnh, lnl, res)


# format of data packet is [SOD|LNH|LNL|COM|byte_data|SUM|ETX]
def format_command(cmd, data):
    SOD = 0x01
    COM = cmd

    if isinstance(data, str):
        byte_data = bytes(data.encode('utf-8'))
    else:
        byte_data = bytes([int(x, 16) for x in data])
    
    LNH, LNL, SUM = calc_sum(int(cmd), data)
    ETX = 0x03
    fmt_header = '<BBBB'
    fmt_footer = 'BB'
    fmt = fmt_header + str(len(data)) + 's' + fmt_footer
    pack = struct.pack(fmt, SOD, LNH, LNL, COM, byte_data, SUM, ETX)
    print(fmt, pack, len(pack))
    return fmt

# format of data packet is [SOD|LNH|LNL|RES|DAT|SUM|ETX]
def format_data(res, data):
    SOD = 0x81
    if (len(data) >= 1024):
        raise Exception(f'Data packet too large, data length is {DATA_LEN} (>1024)')
    LNH, LNL, SUM = calc_sum(int(res), data)
    DAT = bytes([int(x, 16) for x in data])
    RES = res
    ETX = 0x03
    fmt_header = '<BBBB'
    fmt_footer = 'BB'
    fmt = fmt_header + str(len(data)) + 's' + fmt_footer
    pack = struct.pack(fmt, SOD, LNH, LNL, RES, DAT, SUM, ETX)
    print(fmt, pack, len(pack))

# packet received from mcu 
def unpack_header(data):
    header = data[0:4]
    fmt_header = '<BBBB'
    SOD, LNH, LNL, RES = struct.unpack(fmt_header, header)
    if (SOD != 0x81):
        raise Exception(f'Wrong start of packet data received')
    pkt_len = (LNH << 0x8 | LNL) - 1
    if (RES & 0x80):
        raise Exception(f'MCU encountered error {RES & 0x7F}')
    fmt_message = '<' + str(pkt_len) + 's'
    raw = struct.unpack_from(fmt_message, data, 4)[0]
    message = ['0x{:02X}'.format(byte) for byte in raw]
    fmt_footer = '<BB'
    SUM, ETX = struct.unpack_from(fmt_footer, data, 4 + pkt_len)
    lnh, lnl, local_sum = calc_sum(RES, message)
    if (SUM != local_sum):
        raise Exception(f'Sum calculation mismatch, read {local_sum} instead of {SUM}')
    if (ETX != 0x03):
        raise Exception(f'Packet ETX error')
    return message

    

cmd = format_command(INQ_CMD, "")
cmd = format_command(BAU_CMD, ['0x00','0x1E'])
cmd = format_command(IDA_CMD, TESTID)

format_data(0x13, ['0x00','0x01','0x02'])
format_data(0x34, ['0x00'])
format_data(0x00, ['0x00'])
format_data(0x12, ['0x00'])

#print(unpack_header(b'\x81\x00\x02\x08\xC0\x12\x03'))
#print(unpack_header(b'\x81\x00\x03\x08\xC0\xD0\x12\x03'))
print(unpack_header(b'\x81\x00\x02\x00\x00\xFE\x03'))
