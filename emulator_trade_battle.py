#!/usr/bin/python3
import signal
import os
from utilities.bgb_link_cable_server import BGBLinkCableServer
from time import sleep
from utilities.gsc_trading_menu import GSCTradingMenu
from utilities.main_shared_logic import get_connection, get_data_trader_class, start_logic
from utilities.gsc_trading_strings import GSCTradingStrings
import datetime

class PokeTrader:
    SLEEP_TIMER = 0.01
    TIMEOUT_TIMER = 1

    def __init__(self, menu):
        self.curr_recv = None
        self._server = BGBLinkCableServer(self.update_data, menu, kill_function)
        self.connection = get_connection(menu, kill_function)

    def run(self):
        self._server.start()
        self.connection.start()
        
    def update_data(self, data):
        start_time = datetime.datetime.now()
        while self.curr_recv is not None:
            sleep(self.SLEEP_TIMER)
            if (datetime.datetime.now() - start_time).total_seconds() >= self.TIMEOUT_TIMER:
                break
        self.curr_recv = data

    # Code dependant on this connection method
    def sendByte(self, byte_to_send, num_bytes, turbo_transfer = False, **kwargs):
        self._server.turbo_transfer = turbo_transfer
        for i in range(num_bytes):
            self._server.to_send = byte_to_send & 0xFF
            start_time = datetime.datetime.now()
            while self._server.to_send is not None:
                sleep(self.SLEEP_TIMER)
                if (datetime.datetime.now() - start_time).total_seconds() >= self.TIMEOUT_TIMER:
                    break
            byte_to_send = byte_to_send >> 8
        return

    def receiveByte(self, num_bytes):
        recv = 0
        for i in range(num_bytes):
            start_time = datetime.datetime.now()
            while self.curr_recv is None:
                sleep(self.SLEEP_TIMER)
                if (datetime.datetime.now() - start_time).total_seconds() >= self.TIMEOUT_TIMER:
                    self.curr_recv = 0
                    break
            recv |= self.curr_recv << (8*i)
            self.curr_recv = None
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

    trade_c = get_data_trader_class(p.sendByte, p.receiveByte, p.connection, menu, kill_function)
    
    if menu.gen != 3:
        start_logic(trade_c, menu)

menu = GSCTradingMenu(kill_function, is_emulator=True)
menu.handle_menu()
p = PokeTrader(menu)
p.run()
transfer_func(p, menu)
