import sys
import time
import usb.core
import usb.util

MAX_TRANSFER_SIZE = 64

class RAConnect:
    def __init__(self, vendor_id, product_id):
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.ep_in = 0x82
        self.ep_out = 0x02
        self.max_tries = 20
        self.timeout_ms = 100
        self.dev = None
        self.rx_ep = None
        self.tx_ep = None
        self.find_device()

    def find_device(self):
        self.dev = usb.core.find(idVendor=self.vendor_id, idProduct=self.product_id)
        if self.dev is None:
            raise ValueError(f"Device {self.vendor_id}:{self.product_id} not found\nAre you sure it is connected?")

        for config in self.dev:
            for intf in config:
                if usb.util.find_descriptor(config, custom_match=lambda d: (d.bInterfaceClass == 0x02 or d.bInterfaceClass == 0xFF)):
                    print("Found serial device with 0x02 | 0xFF")
                    if self.dev.is_kernel_driver_active(intf.bInterfaceNumber):
                        print("Found kernel driver, detaching ... ")
                        self.dev.detach_kernel_driver(intf.bInterfaceNumber)
                    for ep in intf:
                        if (ep.bmAttributes == 0x02):
                            if ep.bEndpointAddress == self.ep_in:
                                self.rx_ep = ep
                                print(ep)
                            elif ep.bEndpointAddress == self.ep_out:
                                self.tx_ep = ep
                                print(ep)
                    return True

        raise ValueError("Device does not have a serial interface")

    def establish_connection(self):
        for i in range(self.max_tries):
            try:
                self.tx_ep.write(bytes([0x00]), self.timeout_ms)
                ret = self.rx_ep.read(1, self.timeout_ms)
                if ret[0] == 0x00:
                    print("ACK received")
                    return True
            except usb.core.USBError as e:
                print(f"Timeout: retry #{i}", e)
        return False

    def confirm_connection(self):
        for i in range(self.max_tries):
            try:
                self.tx_ep.write(bytes([0x55]), self.timeout_ms)
                ret = self.rx_ep.read(1, self.timeout_ms)
                if ret[0] == 0xC3:
                    print("ACK received")
                    return True
            except usb.core.USBError as e:
                print(f"Timeout: retry #{i}", e)
        return False

    def authenticate_connection(self):
        raise Exception("Not implemented")

    def send_data(self, packed_data):
        if (self.tx_ep == None):
            return False
        try:
            self.tx_ep.write(packed_data, self.timeout_ms)
        except usb.core.USBError as e:
            print(f"Timeout: error", e)
            return False
        return True

    # packets are length 7, except for a read package
    def recv_data(self, exp_len):
        if (exp_len > MAX_TRANSFER_SIZE):
            raise ValueError(f"length package {exp_len} over max transfer size")
        if (self.rx_ep == None):
            return False
        try:
            msg = self.rx_ep.read(exp_len, self.timeout_ms)
        except usb.core.USBError as e:
            print(f"Timeout: error", e)
            return False
        return msg


#communicator = RAConnect(vendor_id=0x1a86, product_id=0x7523)

#communicator.send_data(b'\xAA\xAA\xAA\xAA\xAA\xAA\xAA\xAA\xAA\xAA\xAA')
#communicator.recv_data(7)

#if not communicator.establish_connection():
#    print("Cannot connect")
#    sys.exit(0)
#
#if not communicator.confirm_connection():
#    print("Failed to confirm boot code")
#    sys.exit(0)

