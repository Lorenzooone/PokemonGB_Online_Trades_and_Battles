import usb.core
import usb.util
import signal
import sys
import traceback
import time
import os
import multiboot
import datetime
from time import sleep
from utilities.gsc_trading_menu import GSCTradingMenu
from utilities.gsc_trading_data_utils import GSCUtilsMisc
from utilities.main_shared_logic import get_connection, get_data_trader_class, start_logic
from utilities.gsc_trading_strings import GSCTradingStrings
from utilities.trading_client_type import TradingClientType

dev = None
reattach = False
serial_port = None
epIn = None
epOut = None
epCmd = None
p = None
out_id = None
max_usb_timeout_w = 5
max_usb_timeout_r = 0.1
max_packet_size = 0x40

VID = 0xcafe
PID = 0x4011

# GBLink 2.x firmware
VID_GBLink_2 = 0x2fe3
PID_GBLink_2 = 0x000a

out_id_base = 0
out_id_gblink2 = 1

out_id_names = ["GB Link Port to USB Adapter", "GBLink v2"]

path = "pokemon_gen3_to_genx_mb.gba"
def kill_function():
    os.kill(os.getpid(), signal.SIGINT)
    
class USBGBLink2Trader:
    """
    Class for the GBLink v2.
    """
    SLEEP_TIMER = 0.01

    def __init__(self, receiver = None, sender = None, raw_receiver = None, list_sender = None, is_serial = False, out_id = out_id_base):
        self._receiver = receiver
        self._sender = sender
        self._raw_receiver = raw_receiver
        self._list_sender = list_sender
        self.is_serial = is_serial
        self.out_id = out_id
        self.version = 0
        self.us_between_transfer = 0
        self.bytes_for_transfer = 0
        self.is_device_master = False
        is_bad = (receiver is None) or (sender is None) or (raw_receiver is None)
        if not is_bad:
            print("Connected to: " + out_id_names[self.out_id])

    def can_device_be_master(self):
        # TODO: Add this here once implemented!
        return False

    def update_no_data_default(self, new):
        #TODO: Add implementation
        pass

    def send_section_preambled(self, sending_data, preamble_byte, byte_while_waiting):
        #TODO: Add implementation
        pass

    def get_result_section_preambled_transfer(self):
        #TODO: Add implementation
        return [0]

    def switch_master_of_connection(self, make_device_master):
        #TODO: Add implementation
        self.is_device_master = make_device_master

    def store_version_fw(self):
        # TODO: Add this here! Optional, nice to have
        self.version = 0
        return

    def sender(self, byte_to_send, num_bytes, **kwargs):
        return self._sender(byte_to_send, num_bytes, **kwargs)

    def receiver(self, num_bytes=None):
        if not self.is_device_master:
            return self._receiver(num_bytes = num_bytes)
        while True:
            try:
                out = self._receiver(num_bytes = num_bytes)
                break
            except usb.core.USBTimeoutError as e:
                sleep(self.SLEEP_TIMER)
        return out

    def raw_receiver(self, num_bytes=None):
        if not self.is_device_master:
            return self._raw_receiver(num_bytes = num_bytes)
        while True:
            try:
                out = self._raw_receiver(num_bytes = num_bytes)
                break
            except usb.core.USBTimeoutError as e:
                return []
        return out

    def list_sender(self, data, chunk_size=8, post_transfer_function=None):
        return self._list_sender(data, chunk_size=chunk_size, post_transfer_function=post_transfer_function)

    def get_requires_read_after_write(self):
        # TODO: If this is changed, update it
        return True # Not Async...

    # The 2.x firmware is configured with commands on its own endpoint,
    # instead of the magic packet on the data endpoint
    def reconfigure_fw_function(self, us_between_transfer, bytes_for_transfer):
        if epCmd is None:
            print("\nMISSING EP CMD!\nDisabling firmware reconfiguration!\n")
            return 0

        self.us_between_transfer = us_between_transfer
        self.bytes_for_transfer = bytes_for_transfer

        def cmd(data):
            epCmd.write(bytes(data), timeout=int(max_usb_timeout_w * 1000))
        if bytes_for_transfer == 4:
            cmd([0x40])  # 3.3V for GBA
        else:
            cmd([0x41])  # 5V for GB/GBC
        cmd([0x00, 0x02])  # set GB Link mode
        time.sleep(0.1)  # give the mode time to start
        cmd([0x30, us_between_transfer & 0xFF, (us_between_transfer >> 8) & 0xFF, (us_between_transfer >> 16) & 0xFF, bytes_for_transfer])  # timing config
        return 1
    
class USBToLinkCableTrader:
    """
    Class for the GB Link Port to USB adapter.
    """
    SLEEP_TIMER = 0.01
    # USB Opcodes
    OPCODE_USB_SET_ACTIVE_MODE = 1 # Switch to active mode
    OPCODE_USB_SET_PASSIVE_MODE = 2 # Switch to passive mode
    OPCODE_USB_RESET_PASSIVE_MODE_BUFFERS = 3 # Reset passive mode buffers if an error happens
    OPCODE_USB_SET_PASSIVE_MODE_DEFAULT = 4 # Sets the bytes to send to the host if nothing is enqueued
    OPCODE_USB_SET_PASSIVE_MODE_SECTION_PREAMBLE_WAITING = 5 # Section Preamble mode: prepare preamble_data_to_find, data_waiting_for_preamble
    OPCODE_USB_PASSIVE_MODE_SECTION_GET_CHECKSUM_AND_LEN = 6 # Get length of the data loaded in and checksum, to ensure the transfer went well
    OPCODE_USB_PASSIVE_MODE_SECTION_START = 7 # Start section preamble mode officially
    OPCODE_USB_PASSIVE_MODE_SECTION_GET_IS_DONE_AND_LEN = 8 # Get if the section preamble mode is done, as well as the current length of data out, and in
    OPCODE_USB_RETURN_TO_REGULAR_PASSIVE_MODE = 9 # Return to the regular passive mode from the section preamble mode
    OPCODE_USB_RESET_PASSIVE_MODE = 10 # Reset passive mode entirely in case of an error in bits trasmitted
    OPCODE_USB_PASSIVE_MODE_GET_SECTION_DATA = 11 # Request for some section data

    MAX_TRANSFER_SIZE = 64
    TIMEOUT_LAST_PASSIVE_SECTION_TIMER = 1

    def __init__(self, receiver = None, sender = None, raw_receiver = None, list_sender = None, is_serial = False, out_id = out_id_base):
        self._receiver = receiver
        self._sender = sender
        self._raw_receiver = raw_receiver
        self._list_sender = list_sender
        self.is_serial = is_serial
        self.out_id = out_id
        self.version = 0
        self.us_between_transfer = 0
        self.bytes_for_transfer = 0
        self.is_device_master = False
        is_bad = (receiver is None) or (sender is None) or (raw_receiver is None)
        if not is_bad:
            print("Connected to: " + out_id_names[self.out_id])

    def can_device_be_master(self):
        if self.version < 2:
            return False
        return True

    def update_no_data_default(self, new):
        if self.version < 2:
            return
        multiboot.read_all(self.raw_receiver)

        out_packet = self.get_usb_opcode_list_reconfig_fw() + [self.OPCODE_USB_SET_PASSIVE_MODE_DEFAULT] + GSCUtilsMisc.write_int_le_to_buffer(new)
        self.list_sender(out_packet, chunk_size=len(out_packet))

        val = GSCUtilsMisc.invert_int_endianness(multiboot.read_all(self.raw_receiver) & 0xFFFFFFFF)
        if val != new:
            # Could do something here... Idk...
            pass

    def send_section_preambled(self, sending_data, preamble_byte, byte_while_waiting):
        if self.version < 2:
            return
        done = False
        while not done:
            multiboot.read_all(self.raw_receiver)

            # Send preamble and byte while waiting for preamble
            out_packet = self.get_usb_opcode_list_reconfig_fw() + [self.OPCODE_USB_SET_PASSIVE_MODE_SECTION_PREAMBLE_WAITING] + GSCUtilsMisc.write_int_le_to_buffer(preamble_byte) + GSCUtilsMisc.write_int_le_to_buffer(byte_while_waiting)
            self.list_sender(out_packet, chunk_size=len(out_packet))

            response = multiboot.read_all(self.raw_receiver)
            preamble_byte_read = GSCUtilsMisc.invert_int_endianness((response >> 32) & 0xFFFFFFFF)
            byte_while_waiting_read = GSCUtilsMisc.invert_int_endianness(response & 0xFFFFFFFF)

            # Check matching
            if preamble_byte_read != preamble_byte:
                continue
            if byte_while_waiting_read != byte_while_waiting:
                continue

            # Send data
            self.list_sender(sending_data, chunk_size = self.MAX_TRANSFER_SIZE)

            out_packet = self.get_usb_opcode_list_reconfig_fw() + [self.OPCODE_USB_PASSIVE_MODE_SECTION_GET_CHECKSUM_AND_LEN]
            self.list_sender(out_packet, chunk_size=len(out_packet))

            response = multiboot.read_all(self.raw_receiver)
            checksum_read = GSCUtilsMisc.invert_int_endianness((response >> 32) & 0xFFFFFFFF)
            length_read = GSCUtilsMisc.invert_int_endianness(response & 0xFFFFFFFF)

            calculated_checksum = GSCUtilsMisc.calc_checksum_int_le(sending_data)

            # Check matching
            if length_read != len(sending_data):
                continue
            if checksum_read != calculated_checksum:
                continue

            # Everything matches, send the ok to start sending the section
            out_packet = self.get_usb_opcode_list_reconfig_fw() + [self.OPCODE_USB_PASSIVE_MODE_SECTION_START]
            self.list_sender(out_packet, chunk_size=len(out_packet))

            response = multiboot.read_all(self.raw_receiver)
            if response != self.version:
                continue

            done = True

    def get_result_section_preambled_transfer(self):
        if self.version < 2:
            return [0]
        done = False
        has_encountered_low_left = False
        has_skipped_last = False
        ready_to_read = 0
        while not done:
            multiboot.read_all(self.raw_receiver)

            out_packet = self.get_usb_opcode_list_reconfig_fw() + [self.OPCODE_USB_PASSIVE_MODE_SECTION_GET_IS_DONE_AND_LEN]
            self.list_sender(out_packet, chunk_size=len(out_packet))

            response = multiboot.read_all(self.raw_receiver)
            done = ((response >> 64) & 1) == 1
            ready_to_read = GSCUtilsMisc.invert_int_endianness((response >> 32) & 0xFFFFFFFF)
            missing_write = GSCUtilsMisc.invert_int_endianness(response & 0xFFFFFFFF)

            if (not done) and ((missing_write == 1) or (missing_write == 0)):
                if not has_encountered_low_left:
                    has_encountered_low_left = True
                    start_last = datetime.datetime.now()
                if (datetime.datetime.now() - start_last).total_seconds() >= self.TIMEOUT_LAST_PASSIVE_SECTION_TIMER:
                    done = True
                    if missing_write == 1:
                        has_skipped_last = True

            if not done:
                sleep(self.SLEEP_TIMER)

        # The data is ready to be read back...
        data_received = []
        done = False
        while ready_to_read > 0:
            bytes_to_ask = ready_to_read
            if bytes_to_ask > (self.MAX_TRANSFER_SIZE - 4):
                bytes_to_ask = self.MAX_TRANSFER_SIZE - 4

            out_packet = self.get_usb_opcode_list_reconfig_fw() + [self.OPCODE_USB_PASSIVE_MODE_GET_SECTION_DATA] + GSCUtilsMisc.write_int_le_to_buffer(bytes_to_ask)
            self.list_sender(out_packet, chunk_size=len(out_packet))

            # First read how many bytes have been read
            data_total = self.raw_receiver(num_bytes=bytes_to_ask + 4)
            if len(data_total) < 4:
                break
            data_header = data_total[:4]
            actual_received = GSCUtilsMisc.read_int_le(data_header, 0)
            if (len(data_total) - 4) != actual_received:
                break

            if(actual_received > 0):
                data_received += data_total[4:]
            ready_to_read -= actual_received

            if ready_to_read > 0:
                sleep(self.SLEEP_TIMER)

        if has_skipped_last:
            data_received += [0]

        out_packet = self.get_usb_opcode_list_reconfig_fw() + [self.OPCODE_USB_RETURN_TO_REGULAR_PASSIVE_MODE]
        self.list_sender(out_packet, chunk_size=len(out_packet))

        response = multiboot.read_all(self.raw_receiver)

        return data_received

    def switch_master_of_connection(self, make_device_master):
        if self.version < 2:
            return
        multiboot.read_all(self.raw_receiver)

        out_packet = self.get_usb_opcode_list_reconfig_fw()
        if make_device_master:
            out_packet += [self.OPCODE_USB_SET_PASSIVE_MODE]
        else:
            out_packet += [self.OPCODE_USB_SET_ACTIVE_MODE]
        self.list_sender(out_packet, chunk_size=len(out_packet))

        self.is_device_master = make_device_master
        val = multiboot.read_all(self.raw_receiver)
        if val != self.version:
            # Could do something here... Idk...
            pass

    def sender(self, byte_to_send, num_bytes, **kwargs):
        return self._sender(byte_to_send, num_bytes, **kwargs)

    def receiver(self, num_bytes=None):
        if not self.is_device_master:
            return self._receiver(num_bytes = num_bytes)
        while True:
            try:
                out = self._receiver(num_bytes = num_bytes)
                break
            except usb.core.USBTimeoutError as e:
                sleep(self.SLEEP_TIMER)
        return out

    def raw_receiver(self, num_bytes=None):
        if not self.is_device_master:
            return self._raw_receiver(num_bytes = num_bytes)
        while True:
            try:
                out = self._raw_receiver(num_bytes = num_bytes)
                break
            except usb.core.USBTimeoutError as e:
                return []
        return out

    def list_sender(self, data, chunk_size=8, post_transfer_function=None):
        return self._list_sender(data, chunk_size=chunk_size, post_transfer_function=post_transfer_function)

    def reconfigure_fw_function(self, us_between_transfer, bytes_for_transfer):
        self.us_between_transfer = us_between_transfer
        self.bytes_for_transfer = bytes_for_transfer
        return self.reconfigure_reconfig_fw(us_between_transfer, bytes_for_transfer)

    def get_requires_read_after_write(self):
        return False # Asynchronous

    def get_usb_opcode_list_reconfig_fw(self):
        return [0xCA, 0xFE, 0xCA, 0xFE, 0xCA, 0xFE, 0xCA, 0xFE, 0xCA, 0xFE, 0xCA, 0xFE, 0xCA, 0xFE, 0xCA, 0xFE, 0xDE, 0xAD, 0xBE, 0xEF, 0xDE, 0xAD, 0xBE, 0xEF, 0xDE, 0xAD, 0xBE, 0xEF, 0xDE, 0xAD, 0xBE, 0xEF]

    def get_configure_list_reconfig_fw(self, us_between_transfer, bytes_for_transfer):
        return self.get_usb_opcode_list_reconfig_fw() + [us_between_transfer & 0xFF, (us_between_transfer >> 8) & 0xFF, (us_between_transfer >> 16) & 0xFF, bytes_for_transfer & 0xFF]

    def reconfigure_reconfig_fw(self, us_between_transfer, bytes_for_transfer):
        if self.list_sender is None:
            return 0
        config_base = self.get_configure_list_reconfig_fw(us_between_transfer, bytes_for_transfer)
        self.list_sender(config_base, chunk_size=len(config_base))
        ret = multiboot.read_all(self.raw_receiver)
        if (ret == 1) and (self.version == 0):
           self.version = 1
        return ret

    def store_version_fw(self):
        if self.version == 0:
            return
        list_to_send = self.get_usb_opcode_list_reconfig_fw() + [0xFF, 0xFF, 0xFF, 0xFF]
        multiboot.read_all(self.raw_receiver)
        self.list_sender(list_to_send, chunk_size=len(list_to_send))
        self.version = multiboot.read_all(self.raw_receiver)
        self.reconfigure_fw_function(self.us_between_transfer, self.bytes_for_transfer)
        if self.version >= 2:
            # Restore to a known good state
            self.switch_master_of_connection(False)

def transfer_func(data_transmitter):
    menu = GSCTradingMenu(kill_function)
    menu.handle_menu()
    
    if menu.verbose:
        print(GSCTradingStrings.waiting_transfer_start_str)

    if menu.is_battle is None:
        menu.is_battle = False

    connection = get_connection(menu, kill_function)
    
    if menu.multiboot:
        menu.gen = 3

    if menu.gen == 3:
        us_between_transfer, bytes_for_transfer = 1000, 4
    else:
        us_between_transfer, bytes_for_transfer = 1000, 1

    result = 1
    while result != 0:
        result = multiboot.read_all(data_transmitter.raw_receiver)
    ret = data_transmitter.reconfigure_fw_function(us_between_transfer, bytes_for_transfer)

    if data_transmitter.is_serial and (ret != 1):
        print("WARNING: Firmware not recognized!\nWhen using Serial, you MUST use a firmware which doesn't alter the output!\nIt's best if you update to the one available at:\nhttps://github.com/Lorenzooone/gb-link-firmware-reconfigurable/releases")

    if(menu.gen == 3) and (ret != 1):
        print("Non-reconfigurable firmware found!\nIt's best if you update to the one available at:\nhttps://github.com/Lorenzooone/gb-link-firmware-reconfigurable/releases")
    
    pre_sleep = False
    if(ret == 1) and (menu.gen == 3):
        pre_sleep = True

    data_transmitter.store_version_fw()

    if menu.multiboot:
        multiboot.multiboot(data_transmitter, path)
        return

    trade_c = get_data_trader_class(data_transmitter, connection, menu, kill_function, pre_sleep = pre_sleep)
    connection.start()

    start_logic(trade_c, menu, TradingClientType.python_usb)

# Code dependant on this connection method
def sendByte(byte_to_send, num_bytes, **kwargs):
    epOut.write(byte_to_send.to_bytes(num_bytes, byteorder='big'), timeout=int(max_usb_timeout_w * 1000))
    return

# Code dependant on this connection method
def sendList(data, chunk_size=8, post_transfer_function=None):
    num_iters = int(len(data)/chunk_size)
    for i in range(num_iters):
        epOut.write(data[i*chunk_size:(i+1)*chunk_size], timeout=int(max_usb_timeout_w * 1000))
        if post_transfer_function is not None:
            post_transfer_function(chunk_size)
    #print(num_iters*chunk_size)
    #print(len(data))
    if (num_iters*chunk_size) != len(data):
        epOut.write(data[num_iters*chunk_size:], timeout=int(max_usb_timeout_w * 1000))
        if post_transfer_function is not None:
            post_transfer_function(len(data[num_iters*chunk_size:]))

def receiveByte(num_bytes=None):
    if num_bytes is None:
        num_bytes = max_packet_size
    recv = int.from_bytes(epIn.read(num_bytes, timeout=int(max_usb_timeout_r * 1000)), byteorder='big')
    return recv

def receiveByte_raw(num_bytes=None):
    if num_bytes is None:
        num_bytes = max_packet_size
    return epIn.read(num_bytes, timeout=int(max_usb_timeout_r * 1000))

# Code dependant on this connection method
def sendByte_serial(byte_to_send, num_bytes, **kwargs):
    serial_port.write(byte_to_send.to_bytes(num_bytes, byteorder='big'))
    return

# Code dependant on this connection method
def sendList_serial(data, chunk_size=8, post_transfer_function=None):
    num_iters = int(len(data)/chunk_size)
    for i in range(num_iters):
        serial_port.write(bytes(data[i*chunk_size:(i+1)*chunk_size]))
        if post_transfer_function is not None:
            post_transfer_function(chunk_size)
    #print(num_iters*chunk_size)
    #print(len(data))
    if (num_iters*chunk_size) != len(data):
        serial_port.write(bytes(data[num_iters*chunk_size:]))
        if post_transfer_function is not None:
            post_transfer_function(len(data[num_iters*chunk_size:]))

def receiveByte_serial(num_bytes=None):
    if num_bytes is None:
        num_bytes = max_packet_size
    recv = int.from_bytes(serial_port.read(num_bytes), byteorder='big')
    return recv

def receiveByte_raw_serial(num_bytes=None):
    if num_bytes is None:
        num_bytes = max_packet_size
    return serial_port.read(num_bytes)

# Code dependant on this connection method
def sendByte_win(byte_to_send, num_bytes, **kwargs):
    p.write(byte_to_send.to_bytes(num_bytes, byteorder='big'))

# Code dependant on this connection method
def sendList_win(data, chunk_size=8, post_transfer_function=None):
    #Why? Idk. But it fixes it... :/
    if(chunk_size > 0x3C):
        chunk_size = 0x3C
    num_iters = int(len(data)/chunk_size)
    for i in range(num_iters):
        p.write(bytes(data[i*chunk_size:(i+1)*chunk_size]))
        if post_transfer_function is not None:
            post_transfer_function(chunk_size)
    #print(num_iters*chunk_size)
    #print(len(data))
    if (num_iters*chunk_size) != len(data):
        p.write(bytes(data[num_iters*chunk_size:]))
        if post_transfer_function is not None:
            post_transfer_function(len(data[num_iters*chunk_size:]))

# Code dependant on this connection method
# The original was so slow, I had to rewrite it a bit to make it work for time sensitive applications
def read_win(self, size=None):
    if not self.is_open:
        return None
    rx = [self._rxremaining]
    length = len(self._rxremaining)
    self._rxremaining = b''
    end_timeout = time.time() + (self.timeout or 0.2)
    if size:
        super(ComPort, self).set_timeout(self._ep_in, (self.timeout or 0.2) * 10)
        while length < size:
            c = super(ComPort, self).read(self._ep_in, size-length)
            if c is not None and len(c):
                rx.append(c)
                length += len(c)
                if len(c) == self.maximum_packet_size:
                    end_timeout += (self.timeout or 0.2)
            if time.time() > end_timeout:
                break
    else:
        super(ComPort, self).set_timeout(self._ep_in, (self.timeout or 0.2))
        while True:
            c = super(ComPort, self).read(self._ep_in, self.maximum_packet_size)
            if c is not None and len(c):
                rx.append(c)
                length += len(c)
                if len(c) == self.maximum_packet_size:
                    end_timeout += (self.timeout or 0.2)
                else:
                    break
            else:
                break
            if time.time() > end_timeout:
                break
    chunk = b''.join(rx)
    if size and len(chunk) >= size:
        if self._rxremaining:
            self._rxremaining = chunk[size:] + self._rxremaining
        else:
            self._rxremaining = chunk[size:]
        chunk = chunk[0:size]
    return chunk

def receiveByte_win(num_bytes=None):
    recv = int.from_bytes(read_win(p, size=num_bytes), byteorder='big')
    return recv

def receiveByte_raw_win(num_bytes=None):
    return read_win(p, size=num_bytes)

# Things for the USB connection part
def exit_gracefully():
    if dev is not None:
        usb.util.dispose_resources(dev)
        if(os.name != "nt"):
            if reattach:
                dev.attach_kernel_driver(0)
    if serial_port is not None:
        serial_port.reset_input_buffer()
        serial_port.reset_output_buffer()
        serial_port.close()
    os._exit(1)

def exit_no_device():
    print("Device not found!")
    exit_gracefully()

def signal_handler(sig, frame):
    print("You pressed Ctrl+C!")
    exit_gracefully()

def libusb_method():
    global dev, epIn, epOut, epCmd, out_id, reattach

    devices = list(usb.core.find(find_all=True,idVendor=VID, idProduct=PID))
    for d in devices:
        #print('Device: %s' % d.product)
        dev = d
        try:
            reattach = False
            if(os.name != "nt"):
                if dev.is_kernel_driver_active(0):
                    try:
                        reattach = True
                        dev.detach_kernel_driver(0)
                    except usb.core.USBError as e:
                        sys.exit("Could not detach kernel driver: %s" % str(e))
                else:
                    pass
                    #print("no kernel driver attached")

            dev.set_configuration()

            cfg = dev.get_active_configuration()

            intf = cfg[(2,0)]   # Or find interface with class 0xff

            # Properly handle multiple programs accessing the same device
            usb.util.claim_interface(dev, intf)
            
            dev.reset()

            epIn = usb.util.find_descriptor(
                intf,
                custom_match = \
                lambda e: \
                    usb.util.endpoint_direction(e.bEndpointAddress) == \
                    usb.util.ENDPOINT_IN)

            assert epIn is not None

            epOut = usb.util.find_descriptor(
                intf,
                custom_match = \
                lambda e: \
                    usb.util.endpoint_direction(e.bEndpointAddress) == \
                    usb.util.ENDPOINT_OUT)

            assert epOut is not None

            dev.ctrl_transfer(bmRequestType = 1, bRequest = 0x22, wIndex = 2, wValue = 0x01)
            out_id = out_id_base
            return True

        except:
            pass

    # Try the GBLink 2.x firmware
    devices = list(usb.core.find(find_all=True,idVendor=VID_GBLink_2, idProduct=PID_GBLink_2))
    for d in devices:
        dev = d

        try:
            cfg = dev.get_active_configuration()

            intf = cfg[(0,0)]   # Vendor interface: EP 0x01 commands, EP 0x02/0x82 data

            # Properly handle multiple programs accessing the same device
            usb.util.claim_interface(dev, intf)

            epCmd = usb.util.find_descriptor(intf, custom_match=lambda e: e.bEndpointAddress == 0x01)
            epOut = usb.util.find_descriptor(intf, custom_match=lambda e: e.bEndpointAddress == 0x02)
            epIn = usb.util.find_descriptor(intf, custom_match=lambda e: e.bEndpointAddress == 0x82)

            assert epIn is not None
            assert epOut is not None
            assert epCmd is not None
            out_id = out_id_gblink2
            return True
        except:
            pass

    return False

class WinUsbCDCEPCMD:
    def __init__(self, p):
        self.p = p

    def write(self, data, timeout=1000):
        # Trick ComPort to write to _ep_cmd...
        epOut = self.p._ep_out
        self.p._ep_out = p._ep_cmd
        self.p.write(data)
        self.p._ep_out = epOut

def winusbcdc_method():
    global p, out_id, epCmd
    curr_out_id = out_id_base
    if(os.name == "nt"):
        try:
            print("Trying WinUSB CDC")
            p = ComPort(vid=VID, pid=PID)
            if not p.is_open:
                p = ComPort(vid=VID_GBLink_2, pid=PID_GBLink_2)
                curr_out_id = out_id_gblink2
                if not p.is_open:
                    return False
                # Fix possible issues with maximum_packet_size
                p.change_interface(0)
                int2_desc = p.query_interface_settings(0)
                pipe_list = map(p.query_pipe, range(int2_desc.b_num_endpoints))
                p._ep_out = 2
                p._ep_in = 0x82
                p._ep_cmd = 1
                p.maximum_packet_size = 0xFFFFFFFF
                for item in pipe_list:
                    if (item.pipe_id == p._ep_out) or (item.pipe_id == p._ep_in):
                        p.maximum_packet_size = min(item.maximum_packet_size, p.maximum_packet_size)
                epCmd = WinUsbCDCEPCMD(p)
            #p.baudrate = 115200
            p.settimeout(max_usb_timeout_r)
        except:
            return False
    else:
        return False
    
    out_id = curr_out_id
    return True

def serial_method():
    global serial_port, out_id
    curr_out_id = out_id_base
    try:
        ports = list(serial.tools.list_ports.comports())
        serial_success = False
        port = None
        for device in ports:
            if(device.vid is not None) and (device.pid is not None):
                if(device.vid == VID) and (device.pid == PID):
                    port = device.device
                    break
                if(device.vid == VID_GBLink_2) and (device.pid == PID_GBLink_2):
                    port = device.device
                    curr_out_id = out_id_gblink2
                    break
        if port is None:
            return False
        serial_port = serial.Serial(port=port, bytesize=8, timeout=max_usb_timeout_r, write_timeout = max_usb_timeout_w)
    except Exception as e:
        return False
    out_id = out_id_base
    return True

signal.signal(signal.SIGINT, signal_handler)

try_serial = False
try_libusb = False
try_winusbcdc = False
try:
    import usb.core
    import usb.util
    try_libusb = True
except:
    pass

if(os.name == "nt"):
    try:
        from winusbcdc import ComPort
        try_winusbcdc = True
    except:
        pass
try:
    import serial
    import serial.tools.list_ports
    try_serial = True
except:
    pass

data_transmitter = USBToLinkCableTrader()
found = False
is_serial = False

# The execution path
try:
    if (not found) and try_libusb:
        if(libusb_method()):
            sender = sendByte
            receiver = receiveByte
            raw_receiver = receiveByte_raw
            list_sender = sendList
            found = True
    if (not found) and try_winusbcdc:
        if(winusbcdc_method()):
            sender = sendByte_win
            receiver = receiveByte_win
            raw_receiver = receiveByte_raw_win
            list_sender = sendList_win
            found = True
    if (not found) and try_serial:
        if(serial_method()):
            sender = sendByte_serial
            receiver = receiveByte_serial
            raw_receiver = receiveByte_raw_serial
            list_sender = sendList_serial
            is_serial = True
            found = True

    if found:
        if out_id == out_id_base:
            data_transmitter = USBToLinkCableTrader(sender = sender, receiver = receiver, raw_receiver = raw_receiver, list_sender = list_sender, out_id = out_id, is_serial = is_serial)
        if out_id == out_id_gblink2:
            data_transmitter = USBGBLink2Trader(sender = sender, receiver = receiver, raw_receiver = raw_receiver, list_sender = list_sender, out_id = out_id, is_serial = is_serial)
        print("USB connection established!")
        transfer_func(data_transmitter)
    else:
        print("Couldn't find USB device!")
        missing = ""
        if not try_serial:
            missing += "PySerial, "
        if not try_libusb:
            missing += "PyUSB, "
        if(os.name == "nt") and (not try_winusbcdc):
            missing += "WinUsbCDC, "
        if missing != "":
            print("If the device is attached, try installing " + missing[:-2])
    
    exit_gracefully()
except:
    traceback.print_exc()
    print("Unexpected exception: ", sys.exc_info()[0])
    exit_gracefully()
