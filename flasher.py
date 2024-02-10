import struct

INQ_CMD = 0x00
ERA_CMD = 0x12
WRI_CMD = 0x13
REA_CMD = 0x15
IDA_CMD = 0x30
BAU_CMD = 0x34
SIG_CMD = 0x3A
ARE_CMD = 0x3B

LOW_PULSE = 0x00
GENERIC_CODE = 0x55
BOOT_CODE = 0xC3

TESTID = [
    "0xF0", "0xF1", "0xF2", "0xF3",
    "0xE4", "0xE5", "0xE6", "0xE7",
    "0xD8", "0xD9", "0xDA", "0xDB",
    "0xCC", "0xCD", "0xCE", "0xCF"
]

def calc_sum(data):
    data_len = len(data)
    lnh = data_len + 1 & 0xFF00
    lnl = data_len + 1 & 0x00FF
    res = lnh + lnl
    for i in range(data_len):
            if isinstance(data[i], str):
                res += int(data[i], 16)
            else:
                res += ord(data[i])
    res = ~(res) & 0xFF # two's complement
    return (lnh, lnl, res)


# format of data packet is [SOD|LNH|LNL|COM|byte_data|SUM|ETX]
def format_command(cmd, data):
    SOD = 0x01
    COM = cmd

    if isinstance(data, str):
        byte_data = bytes(data.encode('utf-8'))
    else:
        byte_data = bytes([int(x, 16) for x in data])
    
    LNH, LNL, SUM = calc_sum(data)
    ETX = 0x03
    fmt_header = '<BBBB'
    fmt_footer = 'BB'
    print("sum calculation:", SUM)
    fmt = fmt_header + str(len(data)) + 's' + fmt_footer
    print(fmt)
    pack = struct.pack(fmt, SOD, LNH, LNL, COM, byte_data, SUM, ETX)
    print(pack)
    return fmt

# format of data packet is [SOD|LNH|LNL|RES|DAT|SUM|ETX]
def format_data(data):
    SOD = 0x81
    if (len(data) >= 1024):
        raise Exception(f'Data packet too large, data length is {DATA_LEN} (>1024)')
    LNH, LNL, SUM = calc_sum(data)
    DAT = bytes([int(x, 16) for x in data])
    RES = 0x13
    ETX = 0x03
    fmt_header = '<BBBB'
    fmt_footer = 'BB'
    fmt = fmt_header + str(len(data)) + 's' + fmt_footer
    pack = struct.pack(fmt, SOD, LNH, LNL, RES, DAT, SUM, ETX)
    print(pack)

cmd = format_command(INQ_CMD, "")
print(cmd, struct.calcsize(cmd))

cmd = format_command(BAU_CMD, ['0x00','0x1E'])
print(cmd, struct.calcsize(cmd))

cmd = format_command(IDA_CMD, TESTID)
print(cmd, struct.calcsize(cmd))

format_data(['0x00','0x01','0x02'])



