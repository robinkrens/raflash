from Packer import *

class RADevice:
    def __init__(self, comm, info):
        self.SCI = 0
        self.RMB = 0
        self.NOA = 0x0
        self.TYP = 0x0
        self.BFV = 0x0000

        if (comm == None):
            return
        self.get_info(info)

    def get_info(self, info):
        fmt = '>IIBBH'
        self.SCI, self.RMB, self.NOA, self.TYP, self.BFV = struct.unpack(fmt, info)
        print(f'Ver{self.BFV >> 8}.{self.BFV & 0xFF}')

# test
d = RADevice('a', b'\x01\x31\x2d\x00\x00\x1e\x84\x80\x04\x02\x0a\x08')
