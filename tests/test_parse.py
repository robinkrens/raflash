from src.RAPacker import calc_sum, unpack_pkt, pack_pkt
import pytest

def test_calc_sum():
    assert calc_sum(0x12, ['0x00']) == (0, 0x2, 0xEC)
    assert calc_sum(0x34, ['0x00']) == (0, 0x2, 0xCA)
    assert calc_sum(0x00, ['0x00']) == (0, 0x02, 0xFE)

def test_unpack():
    assert unpack_pkt(b'\x81\x00\x02\x00\x00\xFE\x03') == ['0x00']
    assert unpack_pkt(b'\x81\x00\x02\x12\x00\xEC\x03') == ['0x00']
    assert unpack_pkt(b'\x81\x00\x02\x13\x00\xEB\x03') == ['0x00']

def test_read_unpack():
    assert unpack_pkt(b'\x81\x00\x04\x15\xAA\xBB\xCC\xB6\x03') == ['0xAA', '0xBB', '0xCC']

def test_pack_unpack():
    assert unpack_pkt(pack_pkt(0x13, ['0x00','0x01','0x02'], ack=True)) == ['0x00', '0x01', '0x02']
    assert unpack_pkt(pack_pkt(0x34, ['0x00'], ack=True)) == ['0x00']
    assert unpack_pkt(pack_pkt(0x00, ['0x00'], ack=True)) == ['0x00']
    assert unpack_pkt(pack_pkt(0x12, ['0x00'], ack=True)) == ['0x00']

def test_err_unpack():
    with pytest.raises(ValueError, match=r".*0xC3.*") as excinfo:
        unpack_pkt(b'\x81\x00\x02\x93\xC3\x38\x03')
    assert str(excinfo.value) == 'MCU encountered error 0xC3'
