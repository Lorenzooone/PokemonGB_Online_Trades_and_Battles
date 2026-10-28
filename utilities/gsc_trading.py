import time
import datetime
from random import Random
from .trading_version import TradingVersion
from .gsc_trading_data_utils import *
from .gsc_trading_menu import GSCBufferedNegotiator
from .gsc_trading_strings import GSCTradingStrings
from utilities.trading_client_type import TradingClientType

class GSCTradingClientTransfers:
    full_transfer = "FLL2"
    single_transfer = "SNG2"
    pool_transfer = "POL2"
    pool_transfer_new = "PLN2"
    moves_transfer = "MVS2"
    choice_transfer = "CHC2"
    accept_transfer = "ACP2"
    success_transfer = "SUC2"
    buffered_transfer = "BUF2"
    language_transfer = "LNG2"
    negotiation_transfer = "NEG2"
    client_type_transfer = "CLN2"
    version_client_transfer = "VEC2"
    version_server_transfer = "VES2"
    random_data_transfer = "RAN2"
    need_data_transfer = "ASK2"
    possible_transfers = {
        full_transfer: {0x412, 0x40C, 0x4CC}, # Sum of special_sections_len - Ver 1.0, 2.0 - 4.0, 5.0
        single_transfer: {7, 32}, # Ver 1.0 - 3.0 and 4.0
        pool_transfer: {1 + 0x75 + 1, 1 + 1}, # Counter + Single Pokémon + Egg OR Counter + Fail
        pool_transfer_new: {1 + 0x95 + 1, 1 + 1}, # Counter + Single Pokémon + Egg OR Counter + Fail V5.0
        moves_transfer: {1 + 8}, # Counter + Moves
        choice_transfer : {1 + 1 + 0x75 + 1, 1 + 1 + 0x95 + 1, 1 + 1}, # Counter + Choice + Single Pokémon + Egg OR Counter + Stop
        accept_transfer : {1 + 1}, # Counter + Accept
        success_transfer : {1 + 1}, # Counter + Success
        buffered_transfer : {1 + 1}, # Counter + Buffered or not
        language_transfer : {1}, # Language byte
        negotiation_transfer : {1 + 1}, # Counter + Convergence value
        version_client_transfer : {6}, # Client's version value
        version_server_transfer : {6}, # Server's version value
        client_type_transfer : {4}, # Client type
        random_data_transfer : {10}, # Random values from server
        need_data_transfer : {1 + 1} # Counter + Whether it needs the other player's data
    }

class GSCTradingClient:
    """
    Class which handles sending/receiving trading data
    to/from the other recepient.
    It uses a system of TAGs and IDs.
    """
    base_folder = "useful_data/gsc/"
    transfers_class = GSCTradingClientTransfers
    force_buffered_value = 0x91
    buffered_value = 0x85
    not_buffered_value = 0x12
    need_data_value = 0x72
    not_need_data_value = 0x43
    pool_fail_value = 0x38
    success_value = 0x91
    max_message_id = 255
    max_negotiation_id = 255
    
    def __init__(self, trader, connection, verbose, stop_trade, party_reader, base_no_trade = base_folder + "base.bin", base_pool = base_folder + "base_pool.bin"):
        self.fileBaseTargetName = base_no_trade
        self.fileBasePoolTargetName = base_pool
        self.connection = connection.hll
        self.connection.set_valid_transfers(self.transfers_class.possible_transfers)
        self.stop_trade = stop_trade
        self.received_one = False
        self.party_reader = party_reader
        self.verbose = verbose
        self.connection.prepare_listener(self.transfers_class.full_transfer, self.on_get_big_trading_data)
        self.trader = trader
        self.own_id = None
        self.other_id = None
        self.utils_class = self.get_utils_class()
        
    def get_utils_class(self):
        return GSCUtils
    
    def verbose_print(self, to_print, end='\n'):
        """
        Print if verbose...
        """
        GSCUtilsMisc.verbose_print(to_print, self.verbose, end=end)
    
    def get_server_version(self):
        """
        Handles getting the server's version.
        """
        ret = self.connection.recv_data(self.transfers_class.version_server_transfer)
        if ret is not None:
            ret = TradingVersion.read_version_data(ret)
        return ret
    
    def get_client_version(self):
        """
        Handles getting the other's version.
        """
        ret = self.connection.recv_data(self.transfers_class.version_client_transfer)
        if ret is not None:
            ret = TradingVersion.read_version_data(ret)
        return ret
        
    def send_client_version(self):
        """
        Handles sending my own version.
        """
        self.connection.send_data(self.transfers_class.version_client_transfer, TradingVersion.prepare_version_data())
        
    def reset_client_version(self):
        """
        Handles resetting the version sent to better handle "bad timing".
        """
        self.connection.reset_send(self.transfers_class.version_client_transfer)
    
    def get_random(self):
        """
        Handles getting the RNG values.
        """
        return self.connection.recv_data(self.transfers_class.random_data_transfer)
    
    def get_success(self):
        """
        Handles getting the success trade confirmation value.
        """
        return self.get_single_byte(self.transfers_class.success_transfer)
        
    def send_success(self):
        """
        Handles sending the success trade confirmation value.
        """
        self.send_single_byte(self.transfers_class.success_transfer, self.success_value)
    
    def get_move_data_only(self):
        """
        Handles getting the new move data when only the other player
        has user input.
        It also loads it into the correct pokémon.
        """
        val = self.get_with_counter(self.transfers_class.moves_transfer)
        if val is not None:
            updating_mon = self.trader.other_pokemon.pokemon[self.trader.other_pokemon.get_last_mon_index()]
            data = [updating_mon.get_species()] + val
            self.trader.checks.prepare_species_buffer()
            data = self.trader.checks.apply_checks_to_data(self.trader.checks.moves_checks_map, data)
            for i in range(4):
                updating_mon.set_move(i, data[i+1], max_pp=False)
                updating_mon.set_pp(i, data[i+5])
        return val
        
    def send_move_data_only(self):
        """
        Handles sending the new move data when only the player
        has user input.
        It gets it from the correct pokémon.
        """
        val = [0,0,0,0,0,0,0,0]
        for i in range(4):
            val[i] = self.trader.own_pokemon.pokemon[self.trader.own_pokemon.get_last_mon_index()].get_move(i)
            val[4+i] = self.trader.own_pokemon.pokemon[self.trader.own_pokemon.get_last_mon_index()].get_pp(i)
        self.send_with_counter(self.transfers_class.moves_transfer, val)
    
    def send_with_counter(self, dest, data):
        """
        Sends data with an attached counter to detect passage of steps.
        """
        if self.own_id is None:
            r = Random()
            self.own_id = r.randint(0, self.max_message_id)
        else:
            self.own_id = GSCUtilsMisc.inc_byte(self.own_id)
        self.connection.send_data(dest, [self.own_id] + data)
    
    def get_with_counter(self, dest):
        """
        Gets data and checks the attached counter to make sure it's
        what the program currently expects.
        """
        ret = self.connection.recv_data(dest)
        if ret is not None:
            if self.other_id is None:
                self.other_id = ret[0]
            elif self.other_id != ret[0]:
                return None
            self.other_id = GSCUtilsMisc.inc_byte(self.other_id)
            return ret[1:]
        return ret
    
    def get_single_byte(self, dest):
        """
        Gets data and checks the attached counter to make sure it's
        what the program currently expects. Single byte version.
        """
        ret = self.get_with_counter(dest)
        if ret is not None:
            return ret[0]
        return ret
    
    def send_single_byte(self, dest, byte):
        """
        Sends data with an attached counter to detect passage of steps.
        Single byte version.
        """
        self.send_with_counter(dest, [byte])

    def get_accepted(self):
        """
        Handles getting whether the other player wants to do the trade
        or not.
        """
        return self.get_single_byte(self.transfers_class.accept_transfer)
                
    def send_accepted(self, choice):
        """
        Handles sending whether the player wants to do the trade or not.
        """
        self.send_single_byte(self.transfers_class.accept_transfer, choice)
                
    def get_chosen_mon(self):
        """
        Handles getting which pokémon the other player wants to trade.
        If the sanity checks are on, it also makes sure no weird index
        is selected in case of failure and prepares the data to close
        the current trade offer.
        It's done like this to make it so buffered trading works even
        if the players change their party's order or their moves' order
        between consecutive tries.
        """
        valid = True
        ret = self.get_with_counter(self.transfers_class.choice_transfer)
        
        if ret is not None:
            # Gets the failsafe value. If the sanity checks are on,
            # it cleans it too
            base_index = self.trader.convert_choice(ret[0])
            if ret[0] != self.stop_trade:
                if self.trader.checks.do_sanity_checks and base_index >= self.trader.other_pokemon.get_party_size():
                    base_index = self.trader.other_pokemon.get_last_mon_index()
                
                # Loads the mon and checks that it hasn't changed too much
                actual_data = ret[1:]
                mon = self.utils_class.single_mon_from_data(self.trader.checks, actual_data)
                
                if mon is not None:
                    # Searches for the pokémon. If it's not found, it uses
                    # the failsafe value. If the sanity checks are on,
                    # it will prepare to close the current trade offer
                    found_index = self.trader.other_pokemon.search_for_mon(mon[0], mon[1])
                    if found_index is None:
                        found_index = base_index
                        if self.trader.checks.do_sanity_checks:
                            valid = False
                else:
                    found_index = base_index
                    if self.trader.checks.do_sanity_checks:
                        valid = False

                if not valid:
                    self.verbose_print(GSCTradingStrings.auto_decline_str)
                ret = [self.trader.convert_index(found_index), valid]
            else:
                # Received data for closing the trade
                ret = [ret[0], True]
        return ret

    def generate_chosen_mon_data(self, index):
        return self.utils_class.single_mon_to_data(self.trader.own_pokemon.pokemon[index], self.trader.own_pokemon.is_mon_egg(index), use_new_mail_data = self.trader.is_gen2_new_mail)

    def send_chosen_mon(self, choice):
        """
        Handles sending which pokémon the player wants to trade.
        """
        index = self.trader.convert_choice(choice)
        own_mon = []
        if choice != self.stop_trade:
            if index < self.trader.own_pokemon.get_party_size():
                own_mon = self.generate_chosen_mon_data(index)
        self.send_with_counter(self.transfers_class.choice_transfer, [choice] + own_mon)
    
    def on_get_big_trading_data(self):
        """
        Signals to the user that the buffered trade is ready!
        """
        if not self.received_one:
            self.received_one = True
            self.verbose_print(GSCTradingStrings.received_buffered_data_str.format(kind=self.trader.kind_str))
    
    def reset_big_trading_data(self):
        """
        Make it so if we need to resend stuff, the buffers are clean.
        """
        self.connection.reset_send(self.transfers_class.full_transfer)
        self.connection.reset_recv(self.transfers_class.full_transfer)
        self.received_one = False
        
    def get_big_trading_data(self, lengths):
        """
        Handles getting the other player's entire trading data.
        If it's not ready, it loads a default party in order to get
        the player's entire trading data and prepares the data for 
        closing that trade.
        """
        success = True
        data = self.connection.recv_data(self.transfers_class.full_transfer)
        if data is None:
            success = False
            data = GSCUtilsLoaders.load_trading_data(self.fileBaseTargetName, lengths)
        else:
            data = GSCUtilsMisc.divide_data(data, lengths)
        return data, success

    def send_big_trading_data(self, data):
        """
        Handles sending the player's entire trading data.
        """
        final_data = []
        for i in range(len(data)):
            final_data += data[i]
        self.connection.send_data(self.transfers_class.full_transfer, final_data)
        
    def get_pool_trading_data(self):
        """
        Handles getting the trading data for the mon offered by the server.
        """
        mon = self.get_with_counter(self.transfers_class.pool_transfer_new)
        if mon is not None:
            if len(mon) == 1:
                print(GSCTradingStrings.pool_fail_str)
                self.trader.kill_function()

            # Applies the checks to the received data.
            received_mon = self.utils_class.single_mon_from_data_multilanguage(self.utils_class.get_basic_checks(), mon)
                
            if received_mon is not None:
                # Insert the received mon into a pre-baked party
                mon = self.party_reader(GSCUtilsMisc.read_data(self.fileBasePoolTargetName), do_full=False)
                mon.pokemon += [received_mon[0]]
                
                # Handle max level option
                if received_mon[0].get_level() > self.trader.max_level:
                    received_mon[0].set_level(self.trader.max_level)
                
                # Specially handle the egg party IDs
                if not received_mon[1]:
                    mon.party_info.set_id(0, received_mon[0].get_species())
                    # Handle egg options
                    if (self.trader.menu.egg) and (self.trader.menu.gen == 2):
                        mon.party_info.set_id(0, self.utils_class.egg_id)
                        received_mon[0].set_hatching_cycles()
                        received_mon[0].faint()
                        received_mon[0].set_egg_nickname(self.trader.menu.language)
                elif (not self.trader.menu.egg) and (self.trader.menu.gen == 2) and (received_mon[0].get_hatching_cycles() <= 1):
                    mon.party_info.set_id(0, received_mon[0].get_species())
                    received_mon[0].heal()
                    received_mon[0].set_default_nickname(self.trader.menu.language)
            else:
                mon = None
                    
        return mon
        
    def get_trading_data(self):
        """
        Handles getting the other player's current bytes of trading data.
        """
        return self.connection.recv_data(self.transfers_class.single_transfer)

    def send_trading_data(self, data):
        """
        Handles sending the player's current bytes of trading data.
        """
        self.connection.send_data(self.transfers_class.single_transfer, data)
    
    def send_buffered_data(self, buffered):
        """
        Handles sending the client's choice for the type of trade.
        """
        val = self.not_buffered_value
        if buffered:
            val = self.buffered_value
        if str(buffered) == "Forced":
            val = self.force_buffered_value
        self.send_single_byte(self.transfers_class.buffered_transfer, val)
    
    def get_buffered_data(self):
        """
        Handles getting the other client's choice for the type of trade.
        """
        buffered = None
        val = self.get_single_byte(self.transfers_class.buffered_transfer)
        if val is not None:
            if val == self.buffered_value:
                buffered = True
            elif val == self.not_buffered_value:
                buffered = False
            elif val == self.force_buffered_value:
                buffered = "Forced"
        return buffered
    
    def send_need_data(self, needs_data):
        """
        Handles sending the client's need for new data.
        """
        val = self.not_need_data_value
        if needs_data:
            val = self.need_data_value
        self.send_single_byte(self.transfers_class.need_data_transfer, val)
    
    def get_need_data(self):
        """
        Handles getting the other client's need for new data.
        """
        needs_data = None
        val = self.get_single_byte(self.transfers_class.need_data_transfer)
        if val is not None:
            if val == self.need_data_value:
                needs_data = True
            elif val == self.not_need_data_value:
                needs_data = False
        return needs_data
    
    def send_negotiation_data(self):
        """
        Handles sending the client's convergence value for the type of trade.
        """
        r = Random()
        val = r.randint(0, self.max_negotiation_id)
        self.send_single_byte(self.transfers_class.negotiation_transfer, val)
        return val
    
    def get_negotiation_data(self):
        """
        Handles getting the other client's convergence value
        for the type of trade.
        """
        return self.get_single_byte(self.transfers_class.negotiation_transfer)
    
    def send_language_data(self):
        """
        Handles sending the client's selected language.
        """
        self.connection.send_data(self.transfers_class.language_transfer, [self.trader.menu.language])
    
    def get_language_data(self):
        """
        Handles getting the other client's selected language.
        """
        val = self.connection.recv_data(self.transfers_class.language_transfer)
        if val is None:
            return val
        return val[0]
    
    def send_client_type_data(self, client_type):
        """
        Handles sending the client's type.
        """
        self.connection.send_data(self.transfers_class.client_type_transfer, GSCUtilsMisc.write_int_le_to_buffer(client_type))
    
    def get_client_type_data(self):
        """
        Handles getting the other client's type.
        """
        val = self.connection.recv_data(self.transfers_class.client_type_transfer)
        if val is None:
            return val
        return GSCUtilsMisc.read_int_le(val, 0)

class GSCTrading:
    """
    Class which handles the trading process for the player.
    """
    sleep_timer = 0.02
    option_confirmation_threshold = 10
    resends_limit_trade = 20
    num_bytes_per_transfer = 1
    enter_room_states = [[0x01, 0x61, 0xD1, 0, 0xFE], [{0x61}, {0xD1}, {0}, {0xFE}, {0xFE}]]
    start_trading_states = [[0x75, 0x75, 0x76], [{0x75}, {0}, {0xFD}]]
    success_base_value = 0x70
    success_values = set(range(success_base_value, success_base_value+0x10))
    possible_indexes = set(range(0x70, 0x80))
    fillers = [{}, {}, {}, {}]
    end_of_line = 0x50
    base_mail_index = 3
    mail_message_size_int = 0x21
    mail_message_size_kor = 0x41
    # Size of message is bigger for Korean
    filler_int_mail = {
        mail_message_size_int + (0 * mail_message_size_kor) : [mail_message_size_kor - mail_message_size_int, end_of_line],
        mail_message_size_int + (1 * mail_message_size_kor) : [mail_message_size_kor - mail_message_size_int, end_of_line],
        mail_message_size_int + (2 * mail_message_size_kor) : [mail_message_size_kor - mail_message_size_int, end_of_line],
        mail_message_size_int + (3 * mail_message_size_kor) : [mail_message_size_kor - mail_message_size_int, end_of_line],
        mail_message_size_int + (4 * mail_message_size_kor) : [mail_message_size_kor - mail_message_size_int, end_of_line],
        mail_message_size_int + (5 * mail_message_size_kor) : [mail_message_size_kor - mail_message_size_int, end_of_line],
    }
    # Size of patch set is smaller for Korean
    # Considering the amount of possible bad values,
    # it makes sense...
    filler_kor_mail = {
        0x22E : [0x13, 0],
    }
    old_filler_int_mail = {}
    filler_value = 0xFE00
    articuno_species = 144
    zapdos_species = 145
    moltres_species = 146
    mew_species = 151
    lugia_species = 249
    celebi_species = 251
    special_mons = set([lugia_species, moltres_species, zapdos_species, articuno_species])
    last_filler_value = 0xFEFF
    max_consecutive_no_data = 0x100
    next_section = 0xFD
    mail_next_section = 0x20
    mail_next_section_kor = 0x52
    no_input = 0xFE
    no_input_alternative = 0xFF
    no_data = 0
    total_send_buf_old_bytes = 2
    bytes_per_send_buf_old_byte = 3
    total_send_buf_new_bytes = 8
    bytes_per_send_buf_new_byte = 4
    max_tolerance_bytes = 3
    mail_special_sections_len_old = 0x181
    mail_special_sections_len_new = 0x241
    special_sections_len = [0xA, 0x1BC, 0xC5, mail_special_sections_len_new] #[0xA, 0x1BC, 0xC5, 0x181]
    special_sections_len_old = [0xA, 0x1BC, 0xC5, mail_special_sections_len_old] #[0xA, 0x1BC, 0xC5, 0x181]
    special_sections_starter = [next_section, next_section, next_section, mail_next_section]
    special_sections_preamble_len = [7, 6, 3, 5]
    special_sections_sync = [True, True, True, False]
    mail_drop_bytes_checks_old = 0x181
    drop_bytes_checks = [[0xA, 0x1B9, 0xC5, mail_special_sections_len_new], [next_section, next_section, mail_next_section, no_input], [0,0,0,0]]
    stop_trade = 0x7F
    first_trade_index = 0x70
    decline_trade = 0x71
    accept_trade = 0x72
    
    def __init__(self, sending_func, receiving_func, connection, menu, kill_function, pre_sleep):
        self.sendByte = sending_func
        self.receiveByte = receiving_func
        self.checks = self.get_checks(menu)
        self.comms = self.get_comms(connection, menu)
        self.menu = menu
        self.kill_function = kill_function
        self.extremely_verbose = False
        self.utils_class = self.get_and_init_utils_class()
        self.is_running_compat_3_mode = False
        self.max_seconds_between_transfers = 0.8
        self.pre_sleep = pre_sleep
        self.turbo_transfer = False
        self.heal_after_not_valid_buffered = False
        self.kind_str = GSCTradingStrings.get_kind_str(False)
        self.kind_ing_str = GSCTradingStrings.get_kind_ing_str(False)
    
    def get_and_init_utils_class(self):
        GSCUtils()
        return GSCUtils
    
    def party_reader(self, data, data_mail=None, do_full=True):
        return GSCTradingData(data, data_mail=data_mail, do_full=do_full)
    
    def get_comms(self, connection, menu):
        return GSCTradingClient(self, connection, menu.verbose, self.stop_trade, self.party_reader)
    
    def get_checks(self, menu):
        return GSCChecks(self.special_sections_len, menu.do_sanity_checks, language=menu.language, set_default_nickname = menu.trade_default_pokemon_names, set_default_ot = menu.trade_default_trainer_names, set_default_partner = menu.trade_default_trainer_names, do_profanity_checks = menu.profanity_filter, section_sizes_old = self.special_sections_len_old)
    
    def verbose_print(self, to_print, end='\n'):
        """
        Print if verbose...
        """
        GSCUtilsMisc.verbose_print(to_print, self.menu.verbose, end=end)

    def send_predefined_section(self, states_list, initial_sending=0, die_on_no_data=False):
        """
        Sends a specific and fixed section of data to the player.
        It waits for the next step until it gets to it.
        It can also detect when the player is done trading.
        """
        sending = initial_sending
        consecutive_no_data = 0
        while sending < len(states_list[0]):
            next = states_list[0][sending]
            recv = self.swap_byte(next)
            if(recv in states_list[1][sending]):
                sending += 1
            elif die_on_no_data and (sending == 0):
                if  recv == self.no_data:
                    consecutive_no_data += 1
                    if consecutive_no_data >= self.max_consecutive_no_data:
                        return False
                else:
                    consecutive_no_data = 0
        return True
    
    def act_on_bad_data(self):
        """
        If any byte was dropped, either drop a warning
        or an error depending on kill_on_byte_drops.
        """
        if self.menu.kill_on_byte_drops:
            print(GSCTradingStrings.error_byte_dropped_str.format(kind=self.kind_str))
            self.kill_function()
        elif not self.printed_warning_drop:
            self.verbose_print(GSCTradingStrings.warning_byte_dropped_str.format(kind=self.kind_str))
            self.printed_warning_drop = True
    
    def get_mail_section_id(self):
        return self.base_mail_index

    def get_printable_index(self, index):
        if index != self.get_mail_section_id():
            return index + 1
        return self.base_mail_index + 1
    
    def get_section_length(self, index, buffered):
        if self.is_gen2_new_mail or buffered:
            return self.special_sections_len[index]
        return self.special_sections_len_old[index]

    def get_checker(self, index, buffered):
        if self.is_gen2_new_mail or buffered:
            return self.checks.checks_map[index]
        return self.checks.checks_map_old[index]
    
    def convert_mail_data(self, data, to_device):
        """
        Handles converting the mail data.
        """
        return data

    def update_mail_data(self, data, do_upgrade):
        """
        Handles converting the mail data to the new expanded format.
        """
        if data is None:
            return data

        # The only reason this works so easily is that the relative
        # starting point of the mail patch set hasn't changed...
        # It's still at the end of the message data...

        # Upgrade...
        if do_upgrade:
            if len(data) != self.mail_special_sections_len_old:
                return data
            new_data = []
            for i in range(6):
                pos_start = (i * self.mail_message_size_int)
                new_data += data[pos_start:pos_start + self.mail_message_size_int]
                new_data += ([self.utils_class.end_of_line] * (self.mail_message_size_kor - self.mail_message_size_int))
            pos_start = (6 * self.mail_message_size_int)
            new_data += data[pos_start:]
            data = new_data

        # Downgrade...
        else:
            if len(data) != self.mail_special_sections_len_new:
                return data
            new_data = []
            for i in range(6):
                pos_start = (i * self.mail_message_size_kor)
                new_data += data[pos_start:pos_start + self.mail_message_size_int]
            pos_start = (6 * self.mail_message_size_kor)
            new_data += data[pos_start:]
            data = new_data

        return data
    
    def prevent_no_input_to_list(self, val):
        """
        Sending 0xFE would be problematic!
        """
        if not isinstance(val, list):
            val = [val]
        for i in range(len(val)):
            if val[i] == self.no_input:
                val[i] = self.no_input_alternative
        return val
                    
    def read_section(self, index, send_data, buffered, last_sent, last_index):
        """
        Reads a data section and sends it to the device.
        """
        length = self.get_section_length(index, buffered)
        next = self.special_sections_starter[index]
        checker = self.get_checker(index, buffered)
        
        # Prepare sanity checks stuff
        self.checks.reset_text_buffers()
        self.checks.prepare_patch_sets_buffer()
        self.checks.prepare_species_buffer()

        if not buffered:
            send_buf = self.synch_synch_section_new(index, last_sent, last_index)

        if self.special_sections_sync[index]:
            next = self.no_input

        # Make sure the device is in the right state
        recv = next
        real_section_starter = self.special_sections_starter[index]
        while recv != real_section_starter:
            recv = self.swap_byte(next)

        # Specially handle Korean mail, with its different mail start and length
        from .text_conversions import PokemonNamesForGen
        is_mail_section = index == self.get_mail_section_id()
        changed_language = False
        old_language = self.menu.language
        is_language_kor = self.menu.language == PokemonNamesForGen.KOREAN_LANGUAGE

        next = real_section_starter
        # Random has no leeway, though it's not needed, since master sets the RNG
        if buffered and (index == 0):
            # The "+ 1" is because the first one is not counted...
            for i in range(self.special_sections_preamble_len[index] + 1):
                next = self.swap_byte(next)
                if next != real_section_starter:
                    break
        else:
            # Sync with the device and start the actual trade
            looped_times = 0
            while next == real_section_starter:
                next = self.swap_byte(next)
                # Korean and International/Japanese have different mail starters, detect this
                if is_mail_section and is_language_kor and (next == self.mail_next_section) and (looped_times == 0):
                    real_section_starter = self.mail_next_section
                    self.menu.language = PokemonNamesForGen.ENGLISH_LANGUAGE
                    changed_language = True
                if is_mail_section and (not is_language_kor) and (next == self.mail_next_section_kor) and (looped_times == 0):
                    real_section_starter = self.mail_next_section_kor
                    self.menu.language = PokemonNamesForGen.KOREAN_LANGUAGE
                    changed_language = True
                looped_times += 1

        if changed_language:
            # A ton of things would need to be updated... Just tell them to restart.
            self.verbose_print(GSCTradingStrings.get_different_language_trade_str(old_language, self.menu.language))
            self.kill_function()

        # IMPORTANT: next now contains the first received byte from the device!

        self.verbose_print(GSCTradingStrings.separate_section_str, end='')
        self.turbo_transfer = True
        
        if buffered:
            buf = [next]
            sending_data = None
            if send_data is not None:
                # Separate preparing the data to send from sending it.
                # Prepare the data...
                sending_data = []
                i = 0
                while i < length:
                    sending_data += self.prevent_no_input_to_list(checker[i](send_data[i]))
                    i += 1
                    # Avoid mid-patching issues, check that there are no patches mid-completion...
                    if (i == len(sending_data)) and (i in self.fillers[index].keys()):
                        filler_len = self.fillers[index][i][0]
                        filler_val = self.fillers[index][i][1]
                        for j in range(filler_len):
                            sending_data += self.prevent_no_input_to_list(checker[i + j](send_data[i + j]))
                        i += filler_len

            # Actually send the data...
            # Also covers mirroring with None
            i = 0
            while i < (length-1):
                if sending_data is not None:
                    next = sending_data[i]
                next = self.swap_byte(next)
                self.verbose_print(GSCTradingStrings.transfer_to_hardware_str.format(index=self.get_printable_index(index), completion=GSCTradingStrings.x_out_of_y_str(i, length)), end='')
                buf += [next]
                i += 1

                to_search_filler = len(buf)
                if to_search_filler in self.fillers[index].keys():
                    filler_len = self.fillers[index][to_search_filler][0]
                    filler_val = self.fillers[index][to_search_filler][1]
                    buf += ([filler_val] * filler_len)
                # These are two separate counters, that should proceed separately...
                to_search_filler = i
                if to_search_filler in self.fillers[index].keys():
                    filler_len = self.fillers[index][to_search_filler][0]
                    filler_val = self.fillers[index][to_search_filler][1]
                    i += filler_len

            if sending_data is not None:
                # Send the last byte too
                next = sending_data[length-1]
            self.swap_byte(next)
            self.verbose_print(GSCTradingStrings.transfer_to_hardware_str.format(index=self.get_printable_index(index), completion=GSCTradingStrings.x_out_of_y_str(length, length)), end='')
            for j in range(self.drop_bytes_checks[2][index]):
                self.swap_byte(self.no_data)
            other_buf = sending_data
        else:
            buf, other_buf, last_sent = self.synch_exchange_section_new(next, index, length, checker, send_buf)

        self.turbo_transfer = False
        self.verbose_print(GSCTradingStrings.separate_section_str, end='')
        return buf, other_buf, last_sent
    
    def synch_synch_section_new(self, index, last_sent, last_index):
        # Wait for a connection to be established if it's synchronous
        if last_sent is None:
            send_buf = []
            for i in range(self.total_send_buf_new_bytes):
                send_buf += [[0xFFFF,0xFF, index, False, 0]]
        else:
            min_index = 0
            for i in range(self.total_send_buf_new_bytes):
                if(last_sent[i][0] < last_sent[min_index][0]):
                    min_index = i
                last_sent[min_index] = last_sent[self.total_send_buf_new_bytes - 1]
            last_sent[self.total_send_buf_new_bytes - 1] = [0xFFFF,0xFF, index, False, 0]
            send_buf = last_sent
                
        self.comms.send_trading_data(self.write_entire_data_new(send_buf))
        found = False
        if index == 1:
            self.verbose_print(GSCTradingStrings.waiting_synchro_str)
        while not found:
            received = self.comms.get_trading_data()
            if received is not None:
                recv_buf = self.read_entire_data_new(received)
                if recv_buf[self.total_send_buf_new_bytes - 1] is not None and recv_buf[self.total_send_buf_new_bytes - 1][0] == 0xFFFF:
                    if recv_buf[self.total_send_buf_new_bytes - 1][2] == index: 
                        found = True
                    elif recv_buf[self.total_send_buf_new_bytes - 1][2] != last_index:
                        self.verbose_print(GSCTradingStrings.get_str_language_incompatibility(index, recv_buf[self.total_send_buf_new_bytes - 1][2]))
                        self.kill_function()
            if not found:
                self.sleep_func()
                self.swap_byte(self.no_input)
        if index == 1:
            self.verbose_print(GSCTradingStrings.arrived_synchro_str)
        return send_buf

    def synch_exchange_section_new(self, next, index, length, checker, send_buf):
        # If the trade is synchronous, prepare small send buffers
        self.printed_warning_drop = False
        buf = [next]
        other_buf = []
        recv_data = {}
        real_out = []
        real_in = []
        allowed_max_tolerance_bytes = self.max_tolerance_bytes
        if self.is_new_synch_protocol and (index == 1):
            # The -1 is because of the initial sending offset
            # This is because with (3 + 1) bytes of offset, the last byte
            # of the last mon's nickname doesn't get read by the game...
            allowed_max_tolerance_bytes = self.max_tolerance_bytes - 1
        safety_transfer_amount = allowed_max_tolerance_bytes - 2
        pos_recv = 0
        i = 0
        pos_send = 0
        send_index = 0
        bytes_offset = 1
        bytes_offset_target = allowed_max_tolerance_bytes
        send_buf[send_index] = [pos_send, next, index, False, 0]
        pos_send += 1
        send_index = (send_index + 1) % self.total_send_buf_new_bytes
        last_transfer_time = datetime.datetime.now()
        self.comms.send_trading_data(self.write_entire_data_new(send_buf))
        while i < (length - allowed_max_tolerance_bytes):
            received = self.comms.get_trading_data()
            if received is not None:
                recv_buf = self.read_entire_data_new(received)
                # Get all the bytes we can consecutively send to the device
                recv_data = self.get_swappable_bytes_new(recv_buf, length, index)
                #print("\n" + str(recv_data))
                while pos_recv in recv_data.keys():
                    if pos_recv >= length:
                        break
                    cleaned_byte = self.prevent_no_input_to_list(checker[pos_recv](recv_data[pos_recv]))
                    other_buf += cleaned_byte
                    pos_recv += 1

                    # Avoid mid-patching issues, check that there are no patches mid-completion...
                    if (pos_recv == len(other_buf)) and (pos_recv in self.fillers[index].keys()):
                        filler_len = self.fillers[index][pos_recv][0]
                        filler_val = self.fillers[index][pos_recv][1]
                        added_len = 0
                        for j in range(filler_len):
                            if (pos_recv + j) >= length:
                                break
                            cleaned_byte = self.prevent_no_input_to_list(checker[pos_recv + j](filler_val))
                            other_buf += cleaned_byte
                            added_len += 1
                        pos_recv += added_len
            byte_to_console = self.no_input
            schedule_console = False
            time_diff = datetime.datetime.now() - last_transfer_time
            if time_diff.total_seconds() >= self.max_seconds_between_transfers:
                schedule_console = True
            if bytes_offset < bytes_offset_target:
                schedule_console = True
            elif len(other_buf) > i:
                byte_to_console = other_buf[i]
                if len(other_buf) > (i + safety_transfer_amount):
                    schedule_console = True
                if schedule_console:
                    i += 1
                    if i in self.fillers[index].keys():
                        filler_len = self.fillers[index][i][0]
                        i += filler_len
            
            if schedule_console:
                if byte_to_console == self.no_input:
                    bytes_offset += 1
                    if bytes_offset > allowed_max_tolerance_bytes:
                        self.act_on_bad_data()
                next = self.swap_byte(byte_to_console)
                #print(str(byte_to_console) + "\n" + str(next))
                real_out += [byte_to_console]
                real_in += [next]
                self.verbose_print(GSCTradingStrings.transfer_to_hardware_str.format(index=self.get_printable_index(index), completion=GSCTradingStrings.x_out_of_y_str(i, length)), end='')
                last_transfer_time = datetime.datetime.now()
                send_buf[send_index] = [pos_send, next, index, False, 0]
                send_index = (send_index + 1) % self.total_send_buf_new_bytes
                buf += [next]
                pos_send += 1
                if pos_send in self.fillers[index].keys():
                    filler_len = self.fillers[index][pos_send][0]
                    filler_val = self.fillers[index][pos_send][1]
                    send_buf[send_index] = [pos_send, filler_val, index, True, filler_len]
                    send_index = (send_index + 1) % self.total_send_buf_new_bytes
                    buf += ([filler_val] * filler_len)
                    pos_send += filler_len
                self.comms.send_trading_data(self.write_entire_data_new(send_buf))
            self.sleep_func()

        while i < (length - (bytes_offset)):
            byte_to_console = self.no_data
            i += 1
            schedule_console = True

            if schedule_console:
                next = self.swap_byte(byte_to_console)
                self.verbose_print(GSCTradingStrings.transfer_to_hardware_str.format(index=self.get_printable_index(index), completion=GSCTradingStrings.x_out_of_y_str(i, length)), end='')
                send_buf[send_index] = [pos_send, next, index, False, 0]
                send_index = (send_index + 1) % self.total_send_buf_new_bytes
                pos_send += 1
                self.comms.send_trading_data(self.write_entire_data_new(send_buf))
            self.sleep_func()
        while len(buf) < length:
            buf += [self.no_data]
        while len(other_buf) < length:
            other_buf += [self.no_data]
        self.verbose_print(GSCTradingStrings.transfer_to_hardware_str.format(index=self.get_printable_index(index), completion=GSCTradingStrings.x_out_of_y_str(length, length)), end='')
        return buf, other_buf, send_buf

    def swap_byte(self, send_data):
        """
        Swaps a byte with the device. First send, and then receives.
        It's a high level abstraction which emulates how real hardware works.
        """
        if not self.pre_sleep:
            self.sleep_func()
        self.sendByte(send_data, self.num_bytes_per_transfer, turbo_transfer = self.turbo_transfer)
        recv = self.receiveByte(self.num_bytes_per_transfer)
        if self.extremely_verbose:
            print(GSCTradingStrings.byte_transfer_str.format(send_data=send_data, recv=recv))
        return recv
    
    def create_success_set(self, traded_mons):
        """
        Implements the gen2 anti-cloning measures.
        """
        if(traded_mons[0] == self.mew_species) or (traded_mons[1] == self.mew_species):
            return set([self.success_base_value | 1])
        if(traded_mons[0] == self.celebi_species) or (traded_mons[1] == self.celebi_species):
            return set([self.success_base_value | 2])
        return set([self.success_base_value])
    
    def prepare_single_entry(self, recv_buf, scanning_index, length, index, ret):
        """
        Tries to read a single synchronous entry.
        """
        if recv_buf[scanning_index] is not None:
            if recv_buf[2] >= (index + 1):
                ret[length] = 0
            else:
                byte_num = recv_buf[scanning_index][0]
                if byte_num <= length:
                    ret[byte_num] = recv_buf[scanning_index][1]
                elif byte_num > self.filler_value and byte_num <= self.last_filler_value:
                    # Try to handle fillers by rapidly swapping their bytes
                    previous_scanning_index = (scanning_index+1) & 1
                    total_bytes = byte_num - self.filler_value
                    byte_num = recv_buf[previous_scanning_index][0]
                    for j in range(total_bytes):
                        ret[byte_num + 1 + j] = recv_buf[scanning_index][1]
    
    def prepare_single_entry_new(self, recv_buf, scanning_index, length, index, ret):
        """
        Tries to read a single synchronous entry.
        """
        if recv_buf[scanning_index] is not None:
            if recv_buf[scanning_index][2] > index:
                ret[length] = 0
            else:
                byte_num = recv_buf[scanning_index][0]
                if byte_num <= length:
                    if recv_buf[scanning_index][3]:
                        for j in range(recv_buf[scanning_index][4]):
                            ret[byte_num + j] = recv_buf[scanning_index][1]
                    else:
                        ret[byte_num] = recv_buf[scanning_index][1]
        
    def remove_filler(self, send_buf, curr_byte_num):
        """
        Removes the filler from the send buffer when a new byte is read.
        Also prevents desyncs.
        """
        for i in range(self.total_send_buf_old_bytes):
            byte_num = send_buf[i][0]
            byte_val = send_buf[i][1]
            if byte_num > self.filler_value and byte_num <= self.last_filler_value:
                for j in range(self.total_send_buf_old_bytes):
                    send_buf[j][0] = curr_byte_num
                    send_buf[j][1] = byte_val
    
    def get_swappable_bytes(self, recv_buf, length, index):
        """
        Returns the maximum amount of bytes we can swap freely.
        Tries to speedup the transfer a bit.
        """
        ret = {}
        for i in range(self.total_send_buf_old_bytes):
            self.prepare_single_entry(recv_buf, i, length, index, ret)
        return ret
    
    def get_swappable_bytes_new(self, recv_buf, length, index):
        """
        Returns the maximum amount of bytes we can swap freely.
        Tries to speedup the transfer a bit.
        """
        ret = {}
        for i in range(self.total_send_buf_new_bytes):
            self.prepare_single_entry_new(recv_buf, i, length, index, ret)
        return ret
    
    def read_entire_data_new(self, data):
        final_product = []
        if len(data) < (self.total_send_buf_new_bytes * self.bytes_per_send_buf_new_byte):
            return [None] * self.total_send_buf_new_bytes
        for i in range(self.total_send_buf_new_bytes):
            final_product += [self.read_sync_data_new(data, i * self.bytes_per_send_buf_new_byte)]
        return final_product
        
    def write_entire_data_new(self, data):
        final_product = []
        for i in range(self.total_send_buf_new_bytes):
            final_product += self.write_sync_data_new(data[i])
        return final_product
    
    def read_sync_data_new(self, data, pos):
        if data is not None and len(data) > 0:
            ret_val = [((data[pos]&0x01)<<8) + data[pos+1] + ((data[pos + 3] & 0xC0) << 3), data[pos+2], (data[pos+3] & 0x3F), self.read_is_filler(data[pos]), (data[pos] >> 1) & 0x3F]
            # Prevent issues with older releases
            if ret_val[0] == (0xFFFF & 0x1FF):
                ret_val[0] = 0xFFFF
                ret_val[3] = False
                ret_val[4] = 0
            if ret_val[0] == 0x7FF:
                ret_val[0] = 0x1FF
            return ret_val
        return None
    
    def read_is_filler(self, value):
        if (value >> 7) == 1:
            return True
        return False
    
    def write_is_filler(self, value):
        if value == True:
            return 1 << 7
        return 0 << 7
    
    def write_sync_data_new(self, data):
        # Prevent issues with older releases
        out_val_pos = data[0]
        if out_val_pos == 0x1FF:
            out_val_pos = 0x7FF
        if out_val_pos == 0xFFFF:
            out_val_pos = 0x1FF
        return [((out_val_pos>>8)&0x01) | ((data[4] & 0x3F) << 1) | self.write_is_filler(data[3]), out_val_pos&0xFF, data[1], (data[2] & 0x3F) | ((out_val_pos >> 3) & 0xC0)]
    
    def end_trade(self):
        """
        Forces a currently open trade menu to be closed.
        """
        next = 0
        target = self.stop_trade
        while(next != target):
            next = self.swap_byte(self.stop_trade)
            if(target == self.stop_trade and next == target):
                target = 0

    def wait_for_set_of_values(self, next, values, break_on_no_data = False, threshold = None):
        """
        Waits for the user choosing an option and confirms it's not some
        garbage being sent.
        """
        found_val = next
        consecutive_reads = 0
        special_mode = False
        if threshold is None:
            threshold = self.option_confirmation_threshold
        if threshold == 0:
            # Helps with stuff like BGB lag
            threshold = 1
            special_mode = True
        while consecutive_reads < threshold:
            to_out_byte = self.no_input
            next = self.swap_byte(to_out_byte)
            do_consecutive_reads_check = (next in values) or (break_on_no_data and (next == self.no_data))
            if do_consecutive_reads_check:
                if next == found_val:
                    consecutive_reads += 1
                else:
                    consecutive_reads = 0
                if special_mode:
                    consecutive_reads = threshold
            else:
                consecutive_reads = 0
            found_val = next
        return next
                
    def timed_wait_for_set_of_values(self, next, values, timeout = 1.0, break_on_no_data = False, threshold = None):
        """
        Waits for the user choosing an option and confirms it's not some
        garbage being sent.
        Quits after a specified timeout, returning the last read value...
        """
        start = datetime.datetime.now()
        found_val = next
        consecutive_reads = 0
        special_mode = False
        if threshold is None:
            threshold = self.option_confirmation_threshold
        if threshold == 0:
            # Helps with stuff like BGB lag
            threshold = self.option_confirmation_threshold
            special_mode = True
        while consecutive_reads < threshold:
            to_out_byte = self.no_input
            next = self.swap_byte(to_out_byte)
            do_consecutive_reads_check = (next in values) or (break_on_no_data and (next == self.no_data))
            if do_consecutive_reads_check:
                if next == found_val:
                    consecutive_reads += 1
                else:
                    consecutive_reads = 0
                if special_mode and (next in values):
                    consecutive_reads = threshold
            else:
                consecutive_reads = 0
            found_val = next
            if (datetime.datetime.now() - start).total_seconds() >= timeout:
                break
        return next

    def wait_for_choice(self, next, break_on_no_data = False):
        """
        Waits for an useful value.
        """
        return self.wait_for_set_of_values(next, self.possible_indexes, break_on_no_data=break_on_no_data)

    def timed_wait_for_choice(self, next, timeout = 1.0, break_on_no_data = False, threshold = None):
        """
        Waits for an useful value.
        """
        return self.timed_wait_for_set_of_values(next, self.possible_indexes, timeout=timeout, break_on_no_data=break_on_no_data, threshold=threshold)

    def wait_for_accept_decline(self, next):
        """
        Waits for an useful value.
        """
        return self.wait_for_set_of_values(next, set([self.accept_trade, self.decline_trade]))

    def wait_for_success(self, next, success_values):
        """
        Waits for success.
        """
        return self.wait_for_set_of_values(next, success_values)

    def wait_for_no_data(self, next, resent_byte, limit_resends=0):
        """
        Waits for no_data.
        """
        resends = 0
        while(next != self.no_data):
            next = self.swap_byte(resent_byte)
            if(limit_resends > 0):
                resends += 1
                if(resends == limit_resends):
                    break
        return next

    def wait_for_no_input(self, next):
        """
        Waits for no_input.
        """
        while(next != self.no_input):
            next = self.swap_byte(self.no_input)
        return next

    def timed_wait_for_no_input(self, next, timeout = 1.0):
        """
        Waits for no_input.
        """
        next = self.no_input + 1
        start = datetime.datetime.now()
        while(next != self.no_input):
            next = self.swap_byte(self.no_input)
            time_since_start = (datetime.datetime.now() - start).total_seconds()
            if time_since_start >= timeout:
                break
        return next
        
    def is_choice_decline(self, choice):
        """
        Checks for a trade acceptance decline.
        """
        if choice == self.decline_trade:
            return True
        return False
    
    def get_first_mon(self):
        """
        Returns the first index as the choice.
        """
        return self.first_trade_index, True
    
    def convert_choice(self, choice):
        """
        Converts the menu choice to an index.
        """
        return choice - self.first_trade_index
    
    def convert_index(self, index):
        """
        Converts the index to a menu choice.
        """
        return index + self.first_trade_index

    def is_choice_stop(self, choice):
        """
        Checks for a request to stop the trade.
        """
        if choice == self.stop_trade:
            return True
        return False
    
    def force_receive(self, fun, *args, **kwargs):
        """
        Blocking wait for the requested data.
        It also keeps the device clock running properly.
        """
        received = None
        while received is None:
            self.sleep_func()
            received = fun(*args, **kwargs)
            self.swap_byte(self.no_input)
        return received

    def attempt_receive(self, fun, max_seconds, do_swap_byte = True):
        """
        Blocking wait for the requested data, with timeout
        It also keeps the device clock running properly.
        """
        received = None
        start = datetime.datetime.now()
        while received is None:
            self.sleep_func()
            received = fun()
            if do_swap_byte:
                self.swap_byte(self.no_input)
            if (datetime.datetime.now() - start).total_seconds() > max_seconds:
                break
        return received
    
    def reset_trade(self):
        """
        Reset the trade data...
        """
        self.own_pokemon = None
        self.other_pokemon = None
    
    def check_reset_trade(self, to_server):
        """
        Reset the trade if the data can't be used anymore...
        """
        if to_server or (self.own_blank_trade and self.other_blank_trade):
            # We got here. The other player is in the menu too.
            # Prepare the buffered trade buffers for reuse.
            self.comms.reset_big_trading_data()
            self.reset_trade()
            if not to_server:
                self.verbose_print(GSCTradingStrings.no_recycle_data_str)

    def do_trade(self, get_mon_function, close=False, to_server=False):
        """
        Handles the trading menu.
        """
        trade_completed = False
        base_autoclose = False
        if to_server:
            base_autoclose = True
        autoclose_on_stop = base_autoclose
        
        if close:
            self.verbose_print(GSCTradingStrings.quit_trade_str.format(kind=self.kind_str))

        while not trade_completed:
            # Get the choice
            next = self.no_input
            sent_mon = self.wait_for_choice(next)

            if not close:
                if autoclose_on_stop and self.is_choice_stop(sent_mon):
                    received_choice = self.stop_trade
                else:
                    # Send it to the other player
                    self.verbose_print(GSCTradingStrings.choice_send_str)
                    self.comms.send_chosen_mon(sent_mon)
            
                    # Get the other player's choice
                    if not to_server:
                        self.verbose_print(GSCTradingStrings.choice_recv_str)
                    received_data = self.force_receive(get_mon_function)
                    autoclose_on_stop = base_autoclose
                    received_choice = received_data[0]
                    received_valid = received_data[1]
            else:
                self.reset_trade()
                received_choice = self.stop_trade

            if not self.is_choice_stop(received_choice) and not self.is_choice_stop(sent_mon):
                # Send the other player's choice to the game
                next = self.swap_byte(received_choice)

                # Get whether the trade was declined or not
                next = self.wait_for_no_data(next, received_choice, limit_resends=self.resends_limit_trade)
                if(next == self.no_data):
                    next = self.wait_for_no_input(next)
                accepted = self.wait_for_accept_decline(next)
                
                # Check validity of trade
                valid_trade = received_valid
                if not valid_trade:
                    accepted = self.decline_trade

                if to_server and self.is_choice_decline(accepted):
                    received_accepted = self.decline_trade
                else:
                    # Send it to the other player
                    self.verbose_print(GSCTradingStrings.accepted_send_str.format(accepted_str=GSCTradingStrings.get_accepted_str(self.is_choice_decline(accepted))))
                    self.comms.send_accepted(accepted)
                
                    # Get the other player's choice
                    self.verbose_print(GSCTradingStrings.accepted_wait_str)
                    received_accepted = self.force_receive(self.comms.get_accepted)
                
                # Check validity of trade (if IDs don't match, the game will refuse the trade automatically)
                if not valid_trade:
                    received_accepted = self.decline_trade
                
                # Send the other player's choice to the game
                next = self.swap_byte(received_accepted)

                next = self.wait_for_no_data(next, received_accepted, limit_resends=self.resends_limit_trade)
                if(next == self.no_data):
                    next = self.wait_for_no_input(next)

                if not self.is_choice_decline(received_accepted) and not self.is_choice_decline(accepted):
                    # Apply the trade to the data
                    self.own_pokemon.trade_mon(self.other_pokemon, self.convert_choice(sent_mon), self.convert_choice(received_choice), self.checks)
                    self.own_blank_trade = self.own_pokemon.requires_input(self.own_pokemon.get_last_mon_index(), self.special_mons, self.menu.language, self.menu.language)
                    self.other_blank_trade = self.other_pokemon.requires_input(self.other_pokemon.get_last_mon_index(), self.special_mons, self.other_language, self.menu.language)
                    
                    # Check whether we need to restart entirely.
                    success_set = self.create_success_set(self.own_pokemon.get_traded_mons(self.other_pokemon))
                    success_list = list(success_set)
                    
                    # Check for new data needs
                    if not to_server:
                        self.comms.send_need_data(self.other_blank_trade)
                        self.own_blank_trade = self.force_receive(self.comms.get_need_data)
                    self.check_reset_trade(to_server)

                    # Conclude the trade successfully
                    success_result = self.wait_for_success(next, success_set)

                    # Send it to the other player
                    self.verbose_print(GSCTradingStrings.success_send_str)
                    self.comms.send_success()

                    # Get the other player's choice
                    self.verbose_print(GSCTradingStrings.success_wait_str)
                    self.force_receive(self.comms.get_success)

                    trade_completed = True
                    next = self.swap_byte(success_list[0])
                    next = self.wait_for_no_data(next, success_list[0], limit_resends=self.resends_limit_trade)
                    if(next == self.no_data):
                        next = self.wait_for_no_input(next)
                    self.verbose_print(GSCTradingStrings.restart_trade_str.format(kind=self.kind_str))
                    self.exit_or_new = False
                    
            else:
                if close or (self.is_choice_stop(sent_mon) and self.is_choice_stop(received_choice)):
                    # If both players want to end the trade, do it
                    trade_completed = True
                    self.exit_or_new = True
                    self.verbose_print(GSCTradingStrings.close_str.format(kind=self.kind_str))
                    self.end_trade()
                else:
                    # If one player doesn't want that, get the next values.
                    # Prepare to exit at a moment's notice though...
                    autoclose_on_stop = True
                    self.verbose_print(GSCTradingStrings.close_on_next_str)
                    
                    # Send the other player's choice to the game
                    next = self.swap_byte(received_choice)
                    next = self.wait_for_no_data(next, received_choice, limit_resends=self.resends_limit_trade)
                    if(next == self.no_data):
                        next = self.wait_for_no_input(next)

    def enter_room(self):
        """
        Makes it so the device can enter the trading room.
        """
        self.verbose_print(GSCTradingStrings.enter_trading_room_str.format(kind_ing=self.kind_ing_str))
        self.send_predefined_section(self.enter_room_states)
        self.verbose_print(GSCTradingStrings.entered_trading_room_str.format(kind_ing=self.kind_ing_str))
    
    def sit_to_table(self, initial_sending=0):
        """
        Handles the device sitting at the table.
        """
        if self.exit_or_new:
            self.verbose_print(GSCTradingStrings.sit_table_str)
        return self.send_predefined_section(self.start_trading_states, initial_sending=initial_sending, die_on_no_data=True)

    def get_language_family(self, language):
        from .text_conversions import PokemonNamesForGen
        if language == PokemonNamesForGen.KOREAN_LANGUAGE:
            return 2
        if language == PokemonNamesForGen.JAPANESE_LANGUAGE:
            return 1
        return 0

    def get_language_family_suggestion_str(self, language_family_own, language_family_other):
        return GSCTradingStrings.suggest_trade_language_gen2_str.format(language_one = GSCTradingStrings.get_language_family_to_str(language_family_own), language_two = GSCTradingStrings.get_language_family_to_str(language_family_other))

    def do_version_check(self, do_swap_byte = False):
        self.is_running_compat_3_mode = True
        self.other_language = None
        self.other_client_type = None
        self.is_gen2_new_mail = False
        self.is_new_synch_protocol = False
        self.server_version = self.attempt_receive(self.comms.get_server_version, 5, do_swap_byte = do_swap_byte)
        if self.server_version is not None:
            other_client_version = self.attempt_receive(self.comms.get_client_version, 10, do_swap_byte = do_swap_byte)
            if other_client_version is not None:
                self.is_running_compat_3_mode = False
            if TradingVersion.is_version_greater_equal_than(other_client_version, 4, 2, 0):
                # Unused for now... But send and receive regardless!
                self.other_client_type = self.attempt_receive(self.comms.get_client_type_data, 5, do_swap_byte = do_swap_byte)
                #print(TradingClientType.get_text_for_client_type(self.other_client_type))

                # Used to determine how to patch the text, if needed
                self.other_language = self.attempt_receive(self.comms.get_language_data, 5, do_swap_byte = do_swap_byte)
                # Special case for server, which has all languages
                if self.other_language == 0xFF:
                    self.other_language = None

                self.is_gen2_new_mail = True
                self.is_new_synch_protocol = True
                #print("Version >= 4.2.0")
        if self.is_running_compat_3_mode and (not self.menu.buffered):
            self.verbose_print(GSCTradingStrings.incompatible_version_old_protocol_str)
            self.kill_function()
        if self.other_language is not None:
            if (not self.menu.buffered) and (self.get_language_family(self.other_language) != self.get_language_family(self.menu.language)):
                out_str = self.get_language_family_suggestion_str(self.get_language_family(self.menu.language), self.get_language_family(self.other_language))
                if out_str is not None:
                    self.verbose_print(out_str)
        self.is_version_check_done = True

    def update_mail_data_transfer_based_on_language_and_version(self, buffered):
        from .text_conversions import PokemonNamesForGen
        if self.menu.language == PokemonNamesForGen.JAPANESE_LANGUAGE:
            return
        if self.menu.language != PokemonNamesForGen.KOREAN_LANGUAGE:
            if buffered or self.is_gen2_new_mail:
                self.fillers[self.get_mail_section_id()] = self.filler_int_mail
                self.special_sections_starter[self.get_mail_section_id()] = self.mail_next_section
            else:
                self.fillers[self.get_mail_section_id()] = self.old_filler_int_mail
                self.special_sections_starter[self.get_mail_section_id()] = self.mail_next_section
        else:
            self.fillers[self.get_mail_section_id()] = self.filler_kor_mail
            self.special_sections_starter[self.get_mail_section_id()] = self.mail_next_section_kor
        
    def trade_starting_sequence(self, buffered, send_data = [None, None, None, None]):
        """
        Handles exchanging with the device the three data sections which
        are needed in order to trade.
        Optimizes the synchronous mail_data exchange by executing it only
        if necessary and in the way which requires less packet transfers.
        Returns the player's data and the other player's data.
        """
        # Prepare checks
        self.checks.reset_species_item_list()
        # Send and get the first two sections
        send_data[0] = self.utils_class.base_random_section
        just_sent = None

        while not self.is_version_check_done:
            self.swap_byte(self.no_input)
            self.sleep_func()
        if self.server_version is not None:
            send_data[0] = self.force_receive(self.comms.get_random)

        random_data, random_data_other, just_sent = self.read_section(0, send_data[0], True, just_sent, 0)
        pokemon_data, pokemon_data_other, just_sent = self.read_section(1, send_data[1], buffered, just_sent, 0)
        # Get and apply patches for the Pokémon data
        patches_data, patches_data_other, just_sent = self.read_section(2, send_data[2], buffered, just_sent, 1)
        #GSCUtilsMisc.print_table_hex(pokemon_data)
        #GSCUtilsMisc.print_table_hex(pokemon_data_other)
        #GSCUtilsMisc.print_table_hex(patches_data_other)
        self.utils_class.apply_patches(pokemon_data, patches_data, self.utils_class)
        self.utils_class.apply_patches(pokemon_data_other, patches_data_other, self.utils_class)
        #GSCUtilsMisc.print_table_hex(pokemon_data_other)
                
        pokemon_own = self.party_reader(pokemon_data)
        pokemon_other = self.party_reader(pokemon_data_other)
        pokemon_own_mail = pokemon_own.party_has_mail()
        pokemon_other_mail = pokemon_other.party_has_mail()

        # Trade mail data only if needed
        if (pokemon_own_mail or pokemon_other_mail) or buffered:
            self.update_mail_data_transfer_based_on_language_and_version(buffered)
            #GSCUtilsMisc.print_table_hex(send_data[3])
            send_data[3] = self.convert_mail_data(send_data[3], True)
            #GSCUtilsMisc.print_table_hex(send_data[3])
            mail_data, mail_data_other, just_sent = self.read_section(self.get_mail_section_id(), send_data[3], buffered, just_sent, 2)
            #GSCUtilsMisc.print_table_hex(mail_data)
            #GSCUtilsMisc.print_table_hex(mail_data_other)
            mail_data = self.convert_mail_data(mail_data, False)
            mail_data_other = self.convert_mail_data(mail_data_other, False)
            #GSCUtilsMisc.print_table_hex(mail_data)
            #GSCUtilsMisc.print_table_hex(mail_data_other)
        else:
            send_data[3] = self.utils_class.no_mail_section
            self.verbose_print(GSCTradingStrings.no_mail_other_data_str)
                
            # Exchange mail data with the device
            send_data[3] = self.convert_mail_data(send_data[3], True)
            mail_data, mail_data_other, just_sent = self.read_section(self.get_mail_section_id(), send_data[3], True, just_sent, 2)
            mail_data = self.convert_mail_data(mail_data, False)
            mail_data_other = self.convert_mail_data(mail_data_other, False)

        # Ensure the data can be read properly by us...
        if not self.is_gen2_new_mail:
            mail_data = self.update_mail_data(mail_data, True)
            mail_data_other = self.update_mail_data(mail_data_other, True)
        
        # Apply patches for the mail data
        self.utils_class.apply_patches(mail_data, mail_data, self.utils_class, is_mail=True)
        self.utils_class.apply_patches(mail_data_other, mail_data_other, self.utils_class, is_mail=True)
        
        return [random_data, pokemon_data, mail_data], [random_data_other, pokemon_data_other, mail_data_other]
    
    def synchronous_trade(self):
        """
        Handles launching a synchronous trade.
        Returns True.
        """
        if self.other_pokemon is None:
            data, data_other = self.trade_starting_sequence(False)
        else:
            # Generate the trading data for the device
            # from the other player's one and use it
            self.verbose_print(GSCTradingStrings.recycle_data_str)
            data, data_other = self.trade_starting_sequence(True, send_data=self.other_pokemon.create_trading_data(self.special_sections_len))
        self.own_pokemon = self.party_reader(data[1], data_mail=data[2])
        self.other_pokemon = self.party_reader(data_other[1], data_mail=data_other[2])
        return True

    def get_big_trading_data_recv_lengths(self):
        if self.is_gen2_new_mail:
            return self.special_sections_len
        return self.special_sections_len_old

    def process_obtained_big_trading_data(self, data):
        if self.is_gen2_new_mail:
            return data
        if data is None:
            return data
        if data[3] is None:
            return data
        data[3] = self.update_mail_data(data[3], True)
        return data

    def create_sendable_big_trading_data(self):
        return self.own_pokemon.create_trading_data(self.special_sections_len, is_new_mail_data = self.is_gen2_new_mail)
    
    def buffered_trade(self):
        """
        Handles launching a buffered trade.
        Returns whether the data is the default one or the one
        of another player.
        """
        self.checks.do_sanity_checks = self.menu.do_sanity_checks
        if self.other_pokemon is None:
            data, valid = self.comms.get_big_trading_data(self.get_big_trading_data_recv_lengths())
            if not valid:
                self.verbose_print(GSCTradingStrings.not_received_buffered_data_str.format(kind=self.kind_str))
                self.checks.do_sanity_checks = False
            else:
                self.verbose_print(GSCTradingStrings.found_buffered_data_str.format(kind=self.kind_str))
            data = self.process_obtained_big_trading_data(data)
        else:
            # Generate the trading data for the device
            # from the other player's one and use it
            data = self.other_pokemon.create_trading_data(self.special_sections_len)
            valid = True
            self.verbose_print(GSCTradingStrings.recycle_data_str)
        data, data_other = self.trade_starting_sequence(True, send_data=data)
        self.own_pokemon = self.party_reader(data[1], data_mail=data[2])
        self.own_pokemon.patch_out_bad_chars_for_language_buffered_only(self.menu.language, self.other_language)
        self.other_pokemon = self.party_reader(data_other[1], data_mail=data_other[2])
        if (not valid) and self.heal_after_not_valid_buffered:
            self.own_pokemon.heal_party()
        self.comms.send_big_trading_data(self.create_sendable_big_trading_data())
        return valid

    def player_trade(self, buffered, client_type):
        """
        Handles trading with another player.
        Optimizes the data exchanges by executing them only
        if necessary and in the way which requires less packet transfers.
        """
        self.own_blank_trade = True
        self.other_blank_trade = True
        self.trade_type = GSCTradingStrings.two_player_trade_str
        self.reset_trade()
        self.exit_or_new = True
        self.is_version_check_done = False
        self.is_gen2_new_mail = False
        self.is_new_synch_protocol = False
        self.comms.send_client_version()
        self.comms.send_language_data()
        self.comms.send_client_type_data(client_type)
        buf_neg = GSCBufferedNegotiator(self.menu, self.comms, buffered, self.sleep_func, self.do_version_check)
        buf_neg.start()
        # Start of what the player sees. Enters the room
        self.enter_room()
        while True:
            # Wait for the player to sit to the table
            if not self.sit_to_table():
                break

            # If necessary, start a normal transfer
            if self.own_blank_trade and self.other_blank_trade:
                buffered = self.force_receive(buf_neg.get_chosen_buffered)
                if buffered:
                    valid = self.buffered_trade()
                else:
                    valid = self.synchronous_trade()
            else:
                # If only the other client requires user inputs,
                # wait for its data
                if self.other_blank_trade:
                    self.verbose_print(GSCTradingStrings.move_other_data_str)
                    self.force_receive(self.comms.get_move_data_only)
                else:
                    if self.comms.other_id is not None:
                        self.comms.other_id = GSCUtilsMisc.inc_byte(self.comms.other_id)
                    self.verbose_print(GSCTradingStrings.no_move_other_data_str)
                    
                # Generate the trading data for the device
                # from the other player's one and use it
                self.verbose_print(GSCTradingStrings.reuse_data_str)
                data, data_other = self.trade_starting_sequence(True, send_data=self.other_pokemon.create_trading_data(self.special_sections_len))
                
                # Send this client's data
                self.own_pokemon = self.party_reader(data[1], data_mail=data[2])
                self.verbose_print(GSCTradingStrings.send_move_other_data_str)
                self.comms.send_move_data_only()
            
            self.own_blank_trade = True
            self.other_blank_trade = True
            # Start interacting with the trading menu
            self.do_trade(self.comms.get_chosen_mon, close=not valid)

    def pool_trade(self, client_type):
        """
        Handles trading with the Pool.
        """
        self.own_blank_trade = True
        self.other_blank_trade = True
        self.trade_type = GSCTradingStrings.pool_trade_str
        self.reset_trade()
        self.max_level = self.menu.max_level
        self.is_gen2_new_mail = True
        self.is_new_synch_protocol = True
        self.exit_or_new = True
        self.is_version_check_done = False
        self.other_language = None
        self.menu.buffered = True
        self.comms.send_client_version()
        self.comms.send_language_data()
        self.comms.send_client_type_data(client_type)
        # Start of what the player sees. Enters the room
        self.enter_room()
        while True:
            # Wait for the player to sit to the table
            if not self.sit_to_table():
                break

            # Get data from the server and then use it to start the trade
            if self.other_pokemon is None:
                self.do_version_check()
                self.verbose_print(GSCTradingStrings.pool_receive_data_str)
                self.other_pokemon = self.force_receive(self.comms.get_pool_trading_data)
                self.other_pokemon.patch_out_bad_chars_for_language_buffered_only(None, self.menu.language)
            else:
                self.verbose_print(GSCTradingStrings.pool_recycle_data_str)
            data, data_other = self.trade_starting_sequence(True, send_data=self.other_pokemon.create_trading_data(self.special_sections_len))
            self.own_pokemon = self.party_reader(data[1], data_mail=data[2])

            # Start interacting with the trading menu
            self.do_trade(self.get_first_mon, to_server=True)
        
    # Function needed in order to make sure there is enough time for the slave to prepare the next byte.
    def sleep_func(self, multiplier = 1):
        time.sleep(self.sleep_timer * multiplier)
