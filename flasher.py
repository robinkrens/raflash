import struct

INQ_CMD = 0x00
ERA_CMD = 0x12
WRI_CMD = 0x13
REA_CMD = 0x15
IDA_CMD = 0x30
BAU_CMD = 0x34
SIG_CMD = 0x3A
ARE_CMD = 0x3B

TESTID = [
    "0xF0", "0xF1", "0xF2", "0xF3",
    "0xE4", "0xE5", "0xE6", "0xE7",
    "0xD8", "0xD9", "0xDA", "0xDB",
    "0xCC", "0xCD", "0xCE", "0xCF"
]

def format_command(cmd, data):
    COM_LEN = len(data)
    SOD = 0x01
    COM = cmd
    LNH = COM_LEN + 1 & 0xFF00
    LNL = COM_LEN + 1 & 0x00FF
    calcsum = LNH + LNL

    if isinstance(data, str):
        byte_data = bytes(data.encode('utf-8'))
    else:
        byte_data = bytes([int(x, 16) for x in data])
    
    for i in range(COM_LEN):
            if isinstance(data[i], str):
                calcsum += int(data[i], 16)
            else:
                calcsum += ord(data[i])
    SUM = ~(calcsum) & 0xFF # two's complement
    ETX = 0x03
    fmt_header = '<BBBB'
    fmt_footer = 'BB'
    print("sum calculation:", SUM)
    fmt = fmt_header + str(COM_LEN) + 's' + fmt_footer
    print(fmt)
    pack = struct.pack(fmt, SOD, LNH, LNL, COM, byte_data, SUM, ETX)
    print(pack)
    return fmt

def format_data(data):
    SOD = 0x81
    ETX = 0x03

cmd = format_command(INQ_CMD, "")
print(cmd, struct.calcsize(cmd))

cmd = format_command(BAU_CMD, ['0x00','0x1E'])
print(cmd, struct.calcsize(cmd))

cmd = format_command(IDA_CMD, TESTID)
print(cmd, struct.calcsize(cmd))





