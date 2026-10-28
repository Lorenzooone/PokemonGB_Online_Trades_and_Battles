from .gsc_trading import GSCTrading
from .gsc_trading_jp import GSCTradingJP
from .gsc_trading_kor import GSCTradingKOR
from .gsc_battling import GSCBattling
from .gsc_battling_jp import GSCBattlingJP
from .rby_trading import RBYTrading
from .rby_trading_jp import RBYTradingJP
from .rby_battling import RBYBattling
from .rby_battling_jp import RBYBattlingJP
from .rse_sp_trading import RSESPTrading
from .websocket_client import PoolTradeRunner, ProxyConnectionRunner, ProxyBattleConnectionRunner
from utilities.gsc_trading_strings import GSCTradingStrings
from .text_conversions import PokemonNamesForGen

def start_logic(trade_c, menu, client_type):
    print(GSCTradingStrings.recap_str.format(gen=menu.gen, room=menu.room, recap_option_selected=GSCTradingStrings.get_recap_option_selected(menu)))
    if menu.is_battle:
        trade_c.player_trade(menu.buffered, client_type)
    if menu.trade_type == GSCTradingStrings.two_player_trade_str:
        trade_c.player_trade(menu.buffered, client_type)
    elif menu.trade_type == GSCTradingStrings.pool_trade_str:
        trade_c.pool_trade(client_type)

def get_connection(menu, kill_function):
    connection = None
    if menu.is_battle is None:
        menu.is_battle = False

    if menu.is_battle:
        connection = ProxyBattleConnectionRunner(menu, kill_function)
    elif menu.trade_type == GSCTradingStrings.two_player_trade_str:
        connection = ProxyConnectionRunner(menu, kill_function)
    elif menu.trade_type == GSCTradingStrings.pool_trade_str:
        connection = PoolTradeRunner(menu, kill_function)
    return connection

def get_data_trader_class(data_transmitter, connection, menu, kill_function, pre_sleep = False):
    trade_c = None
    if menu.gen == 2:
        if menu.is_battle:
            if menu.japanese:
                trade_c = GSCBattlingJP(data_transmitter, connection, menu, kill_function, pre_sleep)
            else:
                trade_c = GSCBattling(data_transmitter, connection, menu, kill_function, pre_sleep)
        else:
            if menu.japanese:
                trade_c = GSCTradingJP(data_transmitter, connection, menu, kill_function, pre_sleep)
            elif menu.language == PokemonNamesForGen.KOREAN_LANGUAGE:
                trade_c = GSCTradingKOR(data_transmitter, connection, menu, kill_function, pre_sleep)
            else:
                trade_c = GSCTrading(data_transmitter, connection, menu, kill_function, pre_sleep)
    elif menu.gen == 3:
        trade_c = RSESPTrading(data_transmitter, connection, menu, kill_function, pre_sleep)
    elif menu.gen == 1:
        if menu.is_battle:
            if menu.japanese:
                trade_c = RBYBattlingJP(data_transmitter, connection, menu, kill_function, pre_sleep)
            else:
                trade_c = RBYBattling(data_transmitter, connection, menu, kill_function, pre_sleep)
        else:
            if menu.japanese:
                trade_c = RBYTradingJP(data_transmitter, connection, menu, kill_function, pre_sleep)
            else:
                trade_c = RBYTrading(data_transmitter, connection, menu, kill_function, pre_sleep)
    return trade_c
