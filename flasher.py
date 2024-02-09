import struct

INQ_CMD = 0x00
ERA_CMD = 0x12
WRI_CMD = 0x13
REA_CMD = 0x15
IDA_CMD = 0x30
BAU_CMD = 0x34
SIG_CMD = 0x3A
ARE_CMD = 0x3B

def format_command(cmd, data):
    SOD = 0x01
    COM = cmd
    COM_DATA = bytes(data.encode('utf-8'))
    LNH = len(data) + 1 & 0xFF00
    LNL = len(data) + 1 & 0x00FF
    calcsum = LNH + LNL
    for i in range(len(data)):
            calcsum += ord(data[i])
    SUM = ~(calcsum) & 0xFF # two's complement
    print("sum calculation:", SUM)
    ETX = 0x03
    fmt_header = '<BBBB'
    fmt_footer = 'BB'
    return (fmt_header + str(len(data)) + 's' + fmt_footer)

def format_data(data):
    SOD = 0x81
    ETX = 0x03

cmd = format_command(INQ_CMD, "")
print(cmd, struct.calcsize(cmd))





