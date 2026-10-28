#!/usr/bin/python3
import signal
import os
from utilities.bgb_link_cable_server import BGBLinkCableServer
from time import sleep
from utilities.gsc_trading_menu import GSCTradingMenu
from utilities.main_shared_logic import get_connection, get_data_trader_class, start_logic
from utilities.gsc_trading_strings import GSCTradingStrings
from utilities.trading_client_type import TradingClientType
from threading import Lock
import datetime

class PokeTrader:
    SLEEP_TIMER = 0.01
    SLEEP_TIMER_FAST = 0.001
    TIMEOUT_TIMER = 1
    RECV_BYTES_NONE = 64

    def __init__(self, menu):
        self.curr_recv = []
        self.recv_mutex = Lock()
        self.curr_send = []
        self.send_mutex = Lock()
        self.fast = menu.fast_emu_conn
        self._server = BGBLinkCableServer(self.update_data, self.get_send_data, self.bgb_master_client_data_handler, menu, kill_function)
        self.connection = get_connection(menu, kill_function)
        self.is_bgb_master = False

    def run(self):
        self._server.start()
        self.connection.start()
        
    def update_data(self, data):
        with self.recv_mutex:
            self.curr_recv += [data]
        
    def get_send_data(self):
        if len(self.curr_send) <= 0:
            return None
        out = self.curr_send[0]
        with self.send_mutex:
            self.curr_send = self.curr_send[1:]
        return out
        
    def bgb_master_client_data_handler(self, data):
        if not self.is_bgb_master:
            return None
        self.update_data(data)
        return None

    # Code dependant on this connection method
    def sender(self, byte_to_send, num_bytes, turbo_transfer = False, **kwargs):
        self._server.turbo_transfer = turbo_transfer
        for i in range(num_bytes):
            with self.send_mutex:
                self.curr_send += [byte_to_send & 0xFF]
            byte_to_send = byte_to_send >> 8

        start_time = datetime.datetime.now()
        while len(self.curr_send) > 0:
            sleep_time = self.SLEEP_TIMER
            if self.fast:
                sleep_time = self.SLEEP_TIMER_FAST
            sleep(sleep_time)
            if (datetime.datetime.now() - start_time).total_seconds() >= self.TIMEOUT_TIMER:
                break
        return

    def receiver(self, num_bytes = None):
        recv = int.from_bytes(self.raw_receiver(num_bytes), byteorder='big')
        return recv

    def raw_receiver(self, num_bytes = None):
        if num_bytes is None:
            num_bytes = self.RECV_BYTES_NONE

        start_time = datetime.datetime.now()
        while len(self.curr_recv) < num_bytes:
            sleep_time = self.SLEEP_TIMER
            if self.fast:
                sleep_time = self.SLEEP_TIMER_FAST
            sleep(sleep_time)
            if (datetime.datetime.now() - start_time).total_seconds() >= self.TIMEOUT_TIMER:
                break
        num_to_transfer = num_bytes
        if len(self.curr_recv) < num_to_transfer:
            num_to_transfer = len(self.curr_recv)
        recv = self.curr_recv[:num_to_transfer]
        with self.recv_mutex:
            self.curr_recv = self.curr_recv[num_to_transfer:]
        return recv

def kill_function():
    os.kill(os.getpid(), signal.SIGINT)

def exit_gracefully():
    os._exit(1)

def signal_handler(sig, frame):
    print(GSCTradingStrings.crtlc_str)
    exit_gracefully()

signal.signal(signal.SIGINT, signal_handler)

def transfer_func(p, menu):
    if menu.verbose:
        print(GSCTradingStrings.waiting_transfer_start_str)

    trade_c = get_data_trader_class(p, p.connection, menu, kill_function)
    
    if menu.gen != 3:
        start_logic(trade_c, menu, TradingClientType.python_emu_bgb)

menu = GSCTradingMenu(kill_function, is_emulator=True)
menu.handle_menu()
p = PokeTrader(menu)
p.run()
transfer_func(p, menu)
