from flasher.flasher import calc_sum, unpack_pkt, pack_pkt
import pytest

def test_calc_sum():
    assert calc_sum(0x12, ['0x00']) == (0, 0x2, 0xEC)
    assert calc_sum(0x34, ['0x00']) == (0, 0x2, 0xCA)
    assert calc_sum(0x00, ['0x00']) == (0, 0x02, 0xFE)

def test_unpack():
    assert unpack_pkt(b'\x81\x00\x02\x00\x00\xFE\x03') == ['0x00']
    assert unpack_pkt(b'\x81\x00\x02\x12\x00\xEC\x03') == ['0x00']
    assert unpack_pkt(b'\x81\x00\x02\x13\x00\xEB\x03') == ['0x00']

def test_pack_unpack():
    assert unpack_pkt(pack_pkt(0x13, ['0x00','0x01','0x02'])) == ['0x00', '0x01', '0x02']
    assert unpack_pkt(pack_pkt(0x34, ['0x00'])) == ['0x00']
    assert unpack_pkt(pack_pkt(0x00, ['0x00'])) == ['0x00']
    assert unpack_pkt(pack_pkt(0x12, ['0x00'])) == ['0x00']
