from .gsc_trading import GSCTradingClient, GSCTrading, GSCTradingClientTransfers
from .gsc_trading_data_utils import *
from .trading_version import TradingVersion
from time import sleep
import datetime
from .gsc_trading_menu import GSCBufferedNegotiator
from .gsc_trading_strings import GSCTradingStrings
from inputimeout import inputimeout, TimeoutOccurred

def wait_enter_pressed(ask_str, max_time_s):
    if max_time_s == 0:
        return
    try:
        inputimeout(prompt=ask_str, timeout=max_time_s)
    except TimeoutOccurred:
        print()

class GSCBattlingClientTransfers(GSCTradingClientTransfers):
    battle_full_transfer = "BFL2"
    reseed_server_transfer = "RSS2"
    transfer_sync_transfer = "TST2"

    possible_transfers = GSCTradingClientTransfers.possible_transfers
    possible_transfers[battle_full_transfer] = {1 + 0x40C} # Counter + Sum of special_sections_len
    possible_transfers[reseed_server_transfer] = {1} # ACK from server
    possible_transfers[transfer_sync_transfer] = {1} # ACK to/from other player that it is ready for transfer

class GSCBattlingClient(GSCTradingClient):
    """
    Class which handles sending/receiving trading data
    to/from the other recepient.
    It uses a system of TAGs and IDs.
    """
    base_folder = "useful_data/gsc/"
    transfers_class = GSCBattlingClientTransfers

    def __init__(self, trader, connection, verbose, stop_trade, party_reader, base_no_trade = base_folder + "base_battle.bin", base_pool = base_folder + "base_pool.bin"):
        super(GSCBattlingClient, self).__init__(trader, connection, verbose, stop_trade, party_reader, base_no_trade=base_no_trade, base_pool=base_pool)

    def is_opponent_choice_valid(self, opp_choice):
        if self.trader.is_choice_stop(opp_choice):
            return True

        is_move = self.trader.is_choice_move(opp_choice)
        move_index = self.trader.convert_choice_move(opp_choice)
        is_mon = self.trader.is_choice_mon(opp_choice)
        mon_index = self.trader.convert_choice_mon(opp_choice)

        ret = [opp_choice, valid]

    def get_chosen_option(self):
        """
        Handles getting which pokémon or move the other player wants to do.
        If the sanity checks are on, it also makes sure no weird index
        is selected in case of failure and prepares the data to close
        the current battle.
        It's done like this to make it so buffered trading works even
        if the players change their party's order or their moves' order
        between consecutive tries.
        """
        valid = True
        ret = self.get_with_counter(self.transfers_class.choice_transfer)

        if ret is not None:
            # Gets the failsafe value. If the sanity checks are on,
            # it checks for issues too
            opp_choice = ret[0]
            if not self.trader.is_choice_stop(opp_choice):

                is_move = self.trader.is_choice_move(opp_choice)
                move_index = self.trader.convert_choice_move(opp_choice)
                is_mon = self.trader.is_choice_mon(opp_choice)
                mon_index = self.trader.convert_choice_mon(opp_choice)

                # Sanity checks...
                if self.trader.checks.do_sanity_checks and is_move:
                    valid = self.trader.is_move_usable(self.trader.curr_other_mon_index, move_index, self.trader.other_pokemon)
                if self.trader.checks.do_sanity_checks and is_mon:
                    valid = self.trader.is_mon_usable(mon_index, self.trader.other_pokemon)

                ret = [opp_choice, valid]
            else:
                # Received data for closing the trade
                ret = [opp_choice, True]
        return ret
        
    def send_chosen_option(self, choice):
        """
        Handles sending the battle option...
        """
        self.send_with_counter(self.transfers_class.choice_transfer, [choice])
        
    def get_utils_class(self):
        return GSCUtils
    
    def get_reseed_server(self):
        """
        Handles reseeding the RNG values.
        """
        data = self.connection.recv_data(self.transfers_class.reseed_server_transfer)
        return data
        
    def get_big_battle_trading_data(self, lengths):
        """
        Handles getting the other player's entire trading data with a counter.
        """
        data = None
        data = self.get_with_counter(self.transfers_class.battle_full_transfer)
        if data is not None:
            data = GSCUtilsMisc.divide_data(data, lengths)
        return data

    def send_big_battle_trading_data(self, data, random_data):
        """
        Handles sending the player's entire trading data with a counter.
        """
        final_data = []
        final_data += random_data
        for i in range(1, len(data)):
            final_data += data[i]
        self.send_with_counter(self.transfers_class.battle_full_transfer, final_data)

    def get_transfer_sync_transfer(self):
        """
        Handles getting the other player's confirmation of being ready for
        the synchronous data transfer.
        """
        return self.connection.recv_data(self.transfers_class.transfer_sync_transfer)

    def send_transfer_sync_transfer(self):
        """
        Handles sending the player's confirmation of being ready for
        the synchronous data transfer.
        """
        final_data = [1]
        self.connection.send_data(self.transfers_class.transfer_sync_transfer, final_data)
    
    def reset_transfer_sync_transfer(self):
        """
        Make it so if we need to resend stuff, the confirmations are clean.
        """
        self.connection.reset_send(self.transfers_class.transfer_sync_transfer)
        self.connection.reset_recv(self.transfers_class.transfer_sync_transfer)

class GSCBattling(GSCTrading):
    """
    Class which handles the trading process for the player.
    """
    
    enter_room_states = [[0x01, 0x61, 0xD2, 0, 0xFE], [{0x61}, {0xD2}, {0}, {0xFE}, {0xFE}]]
    start_trading_states = [[0x85, 0x85, 0x86], [{0x85}, {0}, {0xFD}]]
    special_sections_len = [0xA, 0x1BC, 0xC5]
    special_sections_preamble_len = [7, 6, 3]
    next_section = 0xFD
    no_input = 0xFE
    stop_battle = 0x8F
    max_num_pokemon_party = 6
    max_num_moves_pokemon = 4
    first_battle_index = 0x80
    mon_start_index = 0x84
    move_start_index = 0x80
    struggle_index = 0x8E
    unknown_mon_index = 0xFF # When the mon has been swapped out due to whirlwind/roar/metronome
    choice_struggle_id = 0xFF
    move_whirlwind_id = 18
    move_roar_id = 46
    move_fly_id = 19
    move_dig_id = 91
    move_mimic_id = 102
    move_metronome_id = 118
    move_beat_up_id = 251
    drop_bytes_checks = [[0xA, 0x1B9, 0xC5], [next_section, next_section, no_input], [0,0,0]]
    possible_indexes = set(range(0x80, 0x90))
    
    def __init__(self, sending_func, receiving_func, connection, menu, kill_function, pre_sleep):
        super(GSCBattling, self).__init__(sending_func, receiving_func, connection, menu, kill_function, pre_sleep)
        self.curr_own_mon_index = 0
        self.curr_other_mon_index = 0
        self.lock_byte_time_start = datetime.datetime.now()
        self.lock_byte_time_amount = 0
        self.last_random = [0] * self.special_sections_len[0]
        self.can_drop_commands = True
        self.kind_str = GSCTradingStrings.get_kind_str(True)
        self.kind_ing_str = GSCTradingStrings.get_kind_ing_str(True)
        #self.extremely_verbose = True
    
    def get_comms(self, connection, menu):
        return GSCBattlingClient(self, connection, menu.verbose, self.stop_battle, self.party_reader)

    def start_lock_swap(self, timeout):
        """
        Temporarily blocks transfers...
        """
        self.lock_byte_time_start = datetime.datetime.now()
        self.lock_byte_time_amount = timeout

    def stop_lock_swap(self):
        """
        Disable temporarily blocked transfers...
        """
        self.lock_byte_time_amount = 0

    def is_lock_swap_stopped(self):
        """
        Checks if temporarily blocked transfers are disabled...
        """
        return self.lock_byte_time_amount == 0

    def get_lock_swap_remaining_time(self):
        """
        Disable temporarily blocked transfers...
        """
        if self.is_lock_swap_stopped():
            return 0
        if (datetime.datetime.now() - self.lock_byte_time_start).total_seconds() >= self.lock_byte_time_amount:
            return 0
        return self.lock_byte_time_amount - (datetime.datetime.now() - self.lock_byte_time_start).total_seconds()

    def swap_byte(self, send_data):
        """
        Swaps a byte with the device. First send, and then receives.
        It's a high level abstraction which emulates how real hardware works.
        Supports code for blocking transfers temporarily...
        """
        if self.get_lock_swap_remaining_time() > 0:
            return self.no_input
        recv = super().swap_byte(send_data)
        return recv

    def get_user_choice(self):
        """
        Gets the user's choice.
        """
        return self.wait_for_choice(self.no_input, break_on_no_data=True)

    def is_choice_stop(self, choice):
        """
        Checks for a request to stop the trade.
        """
        if choice == self.stop_battle:
            return True
        return False

    def is_choice_move(self, choice):
        """
        Checks if this is a move.
        """
        if choice == self.struggle_index:
            return True
        if choice < self.move_start_index:
            return False
        if choice >= (self.move_start_index + self.max_num_moves_pokemon):
            return False
        return True

    def is_choice_mon(self, choice):
        """
        Checks if this is a mon.
        """
        if choice < self.mon_start_index:
            return False
        if choice >= (self.mon_start_index + self.max_num_pokemon_party):
            return False
        return True
    
    def get_first_mon(self):
        """
        Returns the first index as the choice.
        """
        return self.first_battle_index, True
    
    def convert_choice(self, choice):
        """
        Converts the menu choice to an index.
        """
        return choice - self.first_battle_index
    
    def convert_choice_move(self, choice):
        """
        Converts the menu choice to an index.
        """
        if choice == self.struggle_index:
            return self.choice_struggle_id
        return choice - self.move_start_index
    
    def convert_choice_mon(self, choice):
        """
        Converts the menu choice to an index.
        """
        return choice - self.mon_start_index
    
    def convert_index(self, index):
        """
        Converts the index to a menu choice.
        """
        return index + self.first_battle_index
    
    def convert_index_move(self, index):
        """
        Converts the index to a menu choice.
        """
        if index == self.choice_struggle_id:
            return self.struggle_index
        return index + self.move_start_index
    
    def convert_index_mon(self, index):
        """
        Converts the index to a menu choice.
        """
        return index + self.mon_start_index

    def is_move_unpredictable(self, mon, move_index, battle_data):
        """
        Returns True for unpredictable moves. Returns None for error...
        In GSC, the moves are: Whirlwind, Roar and Metronome...
        If Mimic mimics one of those moves, it can also be a problem.
        """
        # You can always struggle...
        if move_index == self.choice_struggle_id:
            return False
        if move_index >= 4:
            return None

        if mon != self.unknown_mon_index:
            if not self.is_mon_usable(mon, battle_data):
                return None
            if battle_data.pokemon[mon].get_move(move_index) == GSCChecks.free_value_moves:
                return None
            if battle_data.pokemon[mon].get_move(move_index) == self.move_whirlwind_id:
                return True
            if battle_data.pokemon[mon].get_move(move_index) == self.move_roar_id:
                return True
            if battle_data.pokemon[mon].get_move(move_index) == self.move_metronome_id:
                return True
            if battle_data.pokemon[mon].get_move(move_index) == self.move_mimic_id:
                return True
            return False

        # The current Pokemon could be literally whatever, so test everything
        for i in range(battle_data.get_party_size()):
            if battle_data.pokemon[i].get_move(move_index) == self.move_whirlwind_id:
                return True
            if battle_data.pokemon[i].get_move(move_index) == self.move_roar_id:
                return True
            if battle_data.pokemon[i].get_move(move_index) == self.move_metronome_id:
                return True
            if battle_data.pokemon[i].get_move(move_index) == self.move_mimic_id:
                return True

        return False

    def is_move_usable(self, mon, move_index, battle_data):
        """
        Returns True for usable moves. Returns False for error...
        Maybe it could be expanded to also account for PPs, though moves
        like whirlwind, roar and metronome would make that hard.
        """
        # You can always struggle...
        if move_index == self.choice_struggle_id:
            return True
        if move_index >= 4:
            return False
        # The current Pokemon could be literally whatever, so just answer true...
        if mon == self.unknown_mon_index:
            return True

        if not self.is_mon_usable(mon, battle_data):
            return False

        if battle_data.pokemon[mon].get_move(move_index) == GSCChecks.free_value_moves:
            return False

        return True

    def is_mon_usable(self, mon, battle_data):
        """
        Returns True for usable mons. Returns False for error...
        """
        if mon >= battle_data.get_party_size():
            return False

        return True

    def update_battle_information(self, sent_choice, received_choice):
        """
        Updates the battle information of the user and the opponent
        """
        last_turn_own_mon = self.curr_own_mon_index
        last_turn_other_mon = self.curr_other_mon_index

        own_is_move = self.is_choice_move(sent_choice)
        own_move_index = self.convert_choice_move(sent_choice)
        own_is_mon = self.is_choice_mon(sent_choice)
        own_mon_index = self.convert_choice_mon(sent_choice)

        opponent_is_move = self.is_choice_move(received_choice)
        opponent_move_index = self.convert_choice_move(received_choice)
        opponent_is_mon = self.is_choice_mon(received_choice)
        opponent_mon_index = self.convert_choice_mon(received_choice)

        if opponent_is_mon:
            self.curr_other_mon_index = opponent_mon_index

        if own_is_mon:
            self.curr_own_mon_index = own_mon_index

        if own_is_move:
            own_move_unpredictable = self.is_move_unpredictable(last_turn_own_mon, own_move_index, self.own_pokemon)
            if own_move_unpredictable is None:
                own_move_unpredictable = True
            if own_move_unpredictable:
                self.curr_other_mon_index = self.unknown_mon_index

        if opponent_is_move:
            opponent_move_unpredictable = self.is_move_unpredictable(last_turn_other_mon, opponent_move_index, self.other_pokemon)
            if opponent_move_unpredictable is None:
                opponent_move_unpredictable = True
            if opponent_move_unpredictable:
                self.curr_own_mon_index = self.unknown_mon_index

        if self.checks.do_sanity_checks:
            if (last_turn_other_mon != self.curr_other_mon_index) and (self.curr_other_mon_index == self.unknown_mon_index):
                self.verbose_print(GSCTradingStrings.battle_impossible_verify_opponent_moves_str)
            if (last_turn_other_mon != self.curr_other_mon_index) and (last_turn_other_mon == self.unknown_mon_index):
                self.verbose_print(GSCTradingStrings.battle_again_ossible_verify_opponent_moves_str)

    def could_battle_have_ended(self, sent_choice, received_choice):
        """
        In Gen 2, battles start in a specific way...
        These commands can also be regular battle commands
        (i.e. both opponents switch to the 2nd Pokémon of their party).
        Get whether this is the case or not
        """
        if sent_choice not in self.start_trading_states[1][0]:
            return False
        if received_choice not in self.start_trading_states[1][0]:
            return False
        return True

    def has_battle_ended(self, sent_choice, received_choice):
        """
        In Gen 2, battles start in a specific way...
        These commands can also be regular battle commands
        (i.e. both opponents switch to the 2nd Pokémon of their party).
        Check whether it is the start of a new battle or not
        by using a timeout for the answer of the game.
        """
        if not self.could_battle_have_ended(sent_choice, received_choice):
            return False
        next = self.no_input
        next = self.timed_wait_for_set_of_values(next, self.get_battle_end_start_trading_states())
        return next in self.get_battle_end_start_trading_states()

    def get_battle_end_start_trading_states(self):
        return {self.start_trading_states[0][2]}

    def handle_battle_ended_to_new(self):
        self.initial_sit_position = 2
    
    def end_battle(self):
        """
        Forces a currently open battle to be closed.
        """
        next = self.stop_battle
        target = self.no_data
        while(next != target):
            next = self.swap_byte(self.stop_battle)
        
    def battle_starting_sequence(self, buffered, send_data = [None, None, None]):
        """
        Handles exchanging with the device the three data sections which
        are needed in order to battle.
        Returns the player's data and the other player's data.
        """
        # Prepare checks
        self.checks.reset_species_item_list()
        # Send and get the first two sections
        just_sent = None
        while not self.is_version_check_done:
            self.swap_byte(self.no_input)
            self.sleep_func()
        if not buffered:
            self.comms.send_transfer_sync_transfer()
            self.verbose_print(GSCTradingStrings.battle_synchronous_waiting_opponent_transfer_str)
            self.force_receive(self.comms.get_transfer_sync_transfer)
        send_data[0] = self.force_receive(self.comms.get_random)
        self.last_random = send_data[0]

        # Testing time...
        #buffered = True
        #pokemon_base = self.party_reader(None)
        #species_start = 1
        #moves_start = 1
        #for i in range(pokemon_base.get_party_size()):
        #    pokemon_base.pokemon[i] = pokemon_base.mon_generator_class().create_from_scratch(species = species_start + i, moves = [moves_start + (i * 4), moves_start + 1 + (i * 4), moves_start + 2 + (i * 4), moves_start + 3 + (i * 4)])
        #    pokemon_base.party_info.set_id(i, pokemon_base.pokemon[i].get_species())
        #send_data = pokemon_base.create_trading_data(self.special_sections_len)

        random_data, random_data_other, just_sent = self.read_section(0, send_data[0], True, just_sent, 0)
        pokemon_data, pokemon_data_other, just_sent = self.read_section(1, send_data[1], buffered, just_sent, 0)
        # Get and apply patches for the Pokémon data
        patches_data, patches_data_other, just_sent = self.read_section(2, send_data[2], buffered, just_sent, 1)
        self.utils_class.apply_patches(pokemon_data, patches_data, self.utils_class)
        self.utils_class.apply_patches(pokemon_data_other, patches_data_other, self.utils_class)

        if not buffered:
            self.comms.reset_transfer_sync_transfer()

        pokemon_own = self.party_reader(pokemon_data)
        pokemon_other = self.party_reader(pokemon_data_other)
        
        return [random_data, pokemon_data, None], [random_data_other, pokemon_data_other, None]
    
    def trade_starting_sequence(self, buffered, send_data = [None, None, None, None]):
        # Abuse classes to avoid writing duplicated code...
        return self.battle_starting_sequence(buffered, send_data = [send_data[0], send_data[1], send_data[2]])

    def post_buffered_negotiation_init(self):
        self.force_receive(self.comms.get_reseed_server)
        self.do_version_check()

    def do_battle(self, get_mon_function, close=False, to_server=False):
        """
        Handles the trading menu.
        """
        self.initial_sit_position = 0
        battle_completed = False
        base_autoclose = False
        self.curr_own_mon_index = 0
        self.curr_other_mon_index = 0

        if to_server:
            base_autoclose = True
        autoclose_on_stop = base_autoclose
        
        if close:
            self.verbose_print(GSCTradingStrings.quit_trade_str.format(kind=self.kind_str))
        next = self.no_input
        #self.extremely_verbose = True
        while not battle_completed:
            # Get the choice
            # Safety buffer... 30 seconds SEEMS to be enough...
            # Do the check to avoid waiting a ton of time if the time
            # was already waited in another part of the code...
            time_to_wait = self.get_lock_swap_remaining_time()
            if self.is_lock_swap_stopped():
                time_to_wait = self.menu.time_between_battle_turns
                if self.can_drop_commands:
                    self.start_lock_swap(time_to_wait)
            if not self.can_drop_commands:
                time_to_wait = 0
            wait_enter_pressed(GSCTradingStrings.battle_wait_press_enter_str.format(time=int(round(time_to_wait))), time_to_wait)
            self.stop_lock_swap()

            print(GSCTradingStrings.battle_reading_user_input_str)
            sent_choice = self.get_user_choice()

            if sent_choice == self.no_data:
                print(GSCTradingStrings.battle_no_data_str)
                close = True

            if not close:
                if autoclose_on_stop and self.is_choice_stop(sent_choice):
                    received_choice = self.stop_battle
                else:
                    # Send it to the other player
                    self.verbose_print(GSCTradingStrings.choice_send_str)
                    self.comms.send_chosen_option(sent_choice)
            
                    # Get the other player's choice
                    if not to_server:
                        self.verbose_print(GSCTradingStrings.choice_recv_str)
                    received_data = self.force_receive(get_mon_function)
                    autoclose_on_stop = base_autoclose
                    received_choice = received_data[0]
                    received_valid = received_data[1]
                    if not received_valid:
                        print(GSCTradingStrings.battle_problem_command_other_str)
            else:
                self.reset_trade()
                received_choice = self.stop_battle

            # Check if the battle ended, but one of the players was slower to
            # start a new battle...
            if self.could_battle_have_ended(sent_choice, received_choice):
                resent_choice = self.timed_wait_for_choice(next, break_on_no_data=True, threshold=0)
                to_close = False
                if resent_choice == self.no_data:
                    print(GSCTradingStrings.battle_no_data_str)
                    to_close = True
                elif resent_choice == self.no_input:
                    to_close = True
                elif resent_choice != sent_choice: # What?!
                    print(GSCTradingStrings.battle_problem_command_own_str)
                    to_close = True
                if to_close:
                    battle_completed = True
                    self.exit_or_new = True
                    self.verbose_print(GSCTradingStrings.close_str.format(kind=self.kind_str))
                    continue

            if not self.is_choice_stop(received_choice) and not self.is_choice_stop(sent_choice):
                # Send the other player's choice to the game
                next = self.swap_byte(received_choice)

                # Get confirmation that the input was processed by the interrupt
                next = self.wait_for_no_data(next, received_choice, limit_resends=self.resends_limit_trade)
                if(next == self.no_data):
                    next = self.timed_wait_for_no_input(next)

                self.update_battle_information(sent_choice, received_choice)

                # Check if the battle ended, and both players want to quickly
                # start a new battle...
                if self.has_battle_ended(sent_choice, received_choice):
                    self.handle_battle_ended_to_new()
                    battle_completed = True
                    self.exit_or_new = True
                    self.verbose_print(GSCTradingStrings.close_str.format(kind=self.kind_str))
            else:
                if close or (self.is_choice_stop(sent_choice) and self.is_choice_stop(received_choice)):
                    # If both players want to end the battle, do it
                    battle_completed = True
                    self.exit_or_new = True
                    self.verbose_print(GSCTradingStrings.close_str.format(kind=self.kind_str))
                    self.end_battle()
                elif received_choice != self.no_data:                    
                    # Send the other player's choice to the game, will determine
                    # win, loss, or draw.
                    next = self.swap_byte(received_choice)
                    next = self.wait_for_no_data(next, received_choice, limit_resends=self.resends_limit_trade)
                    if(next == self.no_data):
                        next = self.wait_for_no_input(next)
                    battle_completed = True
                    self.exit_or_new = True
                    self.verbose_print(GSCTradingStrings.close_str.format(kind=self.kind_str))

        return

    def player_battle(self, buffered):
        """
        Handles battling with another player.
        Optimizes the data exchanges by executing them only
        if necessary and in the way which requires less packet transfers.
        """
        self.own_blank_trade = True
        self.other_blank_trade = True
        self.initial_sit_position = 0
        self.trade_type = GSCTradingStrings.two_player_battle_str
        self.reset_trade()
        self.stop_lock_swap()
        self.exit_or_new = True
        #buffered = False # Force non-buffered for now...
        self.is_version_check_done = False
        self.comms.send_client_version()
        buf_neg = GSCBufferedNegotiator(self.menu, self.comms, buffered, self.sleep_func, self.post_buffered_negotiation_init, is_battle = True)
        buf_neg.start()
        # Start of what the player sees. Enters the room
        self.enter_room()
        while True:
            # Wait for the player to sit to the table
            if not self.sit_to_table(initial_sending=self.initial_sit_position):
                break

            # Start a normal transfer
            buffered = self.force_receive(buf_neg.get_chosen_buffered)
            if buffered:
                valid = self.buffered_trade()
            else:
                valid = self.synchronous_trade()
            
            self.own_blank_trade = True
            self.other_blank_trade = True
            if valid:
                if self.can_drop_commands:
                    self.start_lock_swap(self.menu.time_between_battle_turns)
                self.comms.send_big_battle_trading_data(self.own_pokemon.create_trading_data(self.special_sections_len), self.last_random)
                other_pokemon_final_full_data = self.force_receive(self.comms.get_big_battle_trading_data, self.special_sections_len)
                other_pokemon_final_data = other_pokemon_final_full_data[1]
                self.utils_class.apply_patches(other_pokemon_final_data, other_pokemon_final_full_data[2], self.utils_class)
                other_pokemon_final = self.party_reader(other_pokemon_final_data)
                success = True
                if self.last_random != other_pokemon_final_full_data[0]:
                    success = False
                if other_pokemon_final.get_party_size() != self.other_pokemon.get_party_size():
                    success = False
                if success:
                    for i in range(other_pokemon_final.get_party_size()):
                        if not other_pokemon_final.pokemon[i].is_equal(self.other_pokemon.pokemon[i], weak=True, all_values=True):
                            success = False
                            break
                if not success:
                    print(GSCTradingStrings.battle_data_error_initial_str)
                    if not buffered:
                        print(GSCTradingStrings.buffered_suggestion_str.format(kind=self.kind_str))
                    break
            # Start interacting with the trading menu
            self.do_battle(self.comms.get_chosen_option, close=not valid)
            self.stop_lock_swap()
            if valid:
                self.comms.reset_big_trading_data()
                self.reset_trade()
                self.force_receive(self.comms.get_reseed_server)

    def player_trade(self, buffered):
        # Abuse classes to avoid writing duplicated code...
        self.player_battle(buffered)
