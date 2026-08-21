from .rby_trading import RBYTradingClient, RBYTradingClientTransfers
from .gsc_battling import GSCBattlingClient, GSCBattling
from .rby_trading_data_utils import RBYUtils, RBYChecks, RBYTradingData

class RBYBattlingClientTransfers(RBYTradingClientTransfers):
    battle_full_transfer = "BFL1"
    reseed_server_transfer = "RSS1"
    transfer_sync_transfer = "TST1"

    possible_transfers = RBYTradingClientTransfers.possible_transfers
    possible_transfers[battle_full_transfer] = {1 + 0x271} # Counter + Sum of special_sections_len
    possible_transfers[reseed_server_transfer] = {1} # ACK from server
    possible_transfers[transfer_sync_transfer] = {1} # ACK to/from other player that it is ready for transfer

class RBYBattlingClient(GSCBattlingClient):
    """
    Class which handles sending/receiving trading data
    to/from the other recepient.
    It uses a system of TAGs and IDs.
    """
    base_folder = "useful_data/rby/"
    transfers_class = RBYBattlingClientTransfers

    def __init__(self, trader, connection, verbose, stop_trade, party_reader, base_no_trade = base_folder + "base_battle.bin", base_pool = base_folder + "base_pool.bin"):
        super(RBYBattlingClient, self).__init__(trader, connection, verbose, stop_trade, party_reader, base_no_trade=base_no_trade, base_pool=base_pool)
        
    def get_utils_class(self):
        return RBYUtils

class RBYBattling(GSCBattling):
    """
    Class which handles the trading process for the player.
    """
    
    enter_room_states = [[0x01, 0x60, 0xD1, 0xD5], [{0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x6F}, {0xD0, 0xD1, 0xD2, 0xD3, 0xD4}, {0xD0, 0xD1, 0xD2, 0xD3, 0xD4}, set(range(0x60, 0x70))]]
    start_trading_states = [[0x60, 0x60], [set(range(0x60, 0x70)), {0xFD}]]
    special_sections_len = [0xA, 0x1A2, 0xC5]
    special_sections_preamble_len = [7, 6, 3]
    next_section = 0xFD
    no_input = 0xFE
    stop_battle = 0x6F
    first_battle_index = 0x60
    mon_start_index = 0x64
    move_start_index = 0x60
    no_move_index = 0x6D
    struggle_index = 0x6E
    choice_no_move_id = 0xFE
    drop_bytes_checks = [[0xA, 0x19F, 0xC5], [next_section, next_section, no_input], [0,0,0]]
    possible_indexes = set(range(0x60, 0x70))
    timeout_user_choice_no_data = 6.0
    
    def __init__(self, sending_func, receiving_func, connection, menu, kill_function, pre_sleep):
        super(RBYBattling, self).__init__(sending_func, receiving_func, connection, menu, kill_function, pre_sleep)
        self.can_drop_commands = False
        self.heal_after_not_valid_buffered = True
        #self.extremely_verbose = True
        
    def get_and_init_utils_class(self):
        RBYUtils()
        return RBYUtils
    
    def party_reader(self, data, data_mail=None, do_full=True):
        return RBYTradingData(data, data_mail=data_mail, do_full=do_full)
    
    def get_comms(self, connection, menu):
        return RBYBattlingClient(self, connection, menu.verbose, self.stop_trade, self.party_reader)
    
    def get_checks(self, menu):
        return RBYChecks(self.special_sections_len, menu.do_sanity_checks)

    def get_user_choice(self):
        """
        Gets the user's choice.
        """
        sent_choice = self.no_input
        while True:
            sent_choice = self.wait_for_choice(self.no_input, break_on_no_data=True)
            if sent_choice != self.no_data:
                return sent_choice
            sent_choice = self.timed_wait_for_no_input(self.no_input, timeout = self.timeout_user_choice_no_data)
            if sent_choice == self.no_data:
                return self.no_data
        return sent_choice

    def is_choice_move(self, choice):
        """
        Checks if this is a move.
        """
        if choice == self.no_move_index:
            return True
        return super().is_choice_move(choice)
    
    def convert_choice_move(self, choice):
        """
        Converts the menu choice to an index.
        """
        if choice == self.no_move_index:
            return self.choice_no_move_id
        return super().convert_choice_move(choice)
    
    def convert_index_move(self, index):
        """
        Converts the index to a menu choice.
        """
        if index == self.choice_no_move_id:
            return self.no_move_index
        return super().convert_index_move(index)

    def is_move_unpredictable(self, mon, move_index, battle_data):
        """
        Returns True for unpredictable moves. Returns None for error...
        In RBY, there are no unpredictable moves... I think?
        """
        return False

    def is_move_usable(self, mon, move_index, battle_data):
        """
        Returns True for usable moves. Returns False for error...
        Maybe it could be expanded to also account for PPs...
        """
        # You can always do nothing...
        # Caused by moves like wrap.
        if move_index == self.choice_no_move_id:
            return True
        return super().is_move_usable(mon, move_index, battle_data)

    def get_battle_end_start_trading_states(self):
        return self.start_trading_states[1][1]

    def handle_battle_ended_to_new(self):
        self.initial_sit_position = 1
