
class GSCTradingStrings:
    """
    Class which collects all the text used by the program
    and methods connected to that.
    """
    version_str = "Version: {major}.{minor}.{build}"
    buffered_str = "Buffered"
    synchronous_str = "Synchronous"
    kind_trade_str = "trade"
    kind_trading_str = "trading"
    kind_battle_str = "battle"
    send_request = "S"
    get_request = "G"
    set_japanese_str = "Set game as Japanese (Current: International)"
    unset_japanese_str = "Set game as International (Current: Japanese)"
    set_egg_str = "Convert received Pokémon to eggs (Current: Do nothing)"
    unset_egg_str = "Don't convert received Pokémon to eggs (Current: Turn to Eggs)"
    unset_japanese_str = "Set game as International (Current: Japanese)"
    active_sanity_checks_str = "Disable Sanity checks (Current: Enabled)"
    inactive_sanity_checks_str = "Enable Sanity checks (Current: Disabled)"
    active_kill_on_byte_drops_str = "Disable Crash on synchronous byte drop (Current: Enabled)"
    inactive_kill_on_byte_drops_str = "Enable Crash on synchronous byte drop (Current: Disabled)"
    websocket_client_error_str = 'Websocket client error:'
    connection_dropped_str = 'Connection dropped'
    p2p_listening_str = 'Listening on {host}:{port}...'
    p2p_server_str = 'Received connection from {host}:{port}'
    bgb_listening_str = 'Listening for bgb on {host}:{port}...'
    bgb_server_str = 'Received bgb connection from {host}:{port}'
    p2p_client_str = 'Connecting to {host}:{port}...'
    socket_error_str = 'Socket error:'
    index_error_str = "Index error!"
    io_error_str = "I/O error({0}): {1}"
    unknown_error_str = "Unexpected error:"
    unrecognized_character_str = "UNRECOGNIZED CHARACTER: {letter}"
    buffered_suggestion_str = "\nIf this happens often, you might want to do a Buffered {kind} instead!"
    error_byte_dropped_str = "\nError! At least one byte was not properly transfered!" + buffered_suggestion_str
    warning_byte_dropped_str = "\nWarning! At least one byte was not properly transfered!" + buffered_suggestion_str
    byte_transfer_str = "{send_data} - {recv}"
    crtlc_str = 'You pressed Ctrl+C!'
    waiting_transfer_start_str = "Waiting for the transfer to start..."
    enter_trading_room_str = "\nPlease enter the {kind_ing} room..."
    entered_trading_room_str = "\nEntered the {kind_ing} room..."
    sit_table_str = "\nYou can now either sit at the table, or quit the room..."
    buffered_sit_table_str = "Please sit at the table to send to the other player your {kind_ing} data."
    not_received_buffered_data_str = "\nThe other player has not sent their buffered data yet.\nStarting a {kind} in order to get your data, so the other player can use it."
    found_buffered_data_str = "\nFound the other player's data.\nStarting the {kind} and sending your data to them, if they don't have it yet."
    recycle_data_str = "\nReusing the previously received data."
    choice_send_str = "\nSending your choice."
    choice_recv_str = "\nWaiting for the other player's choice..."
    accepted_send_str = "\nSending {accepted_str}."
    accepted_wait_str = "\nWaiting for the answer..."
    success_send_str = "\nSending trade confirmation..."
    success_wait_str = "\nWaiting for trade confirmation..."
    close_str = "\nClosing the {kind}..."
    close_on_next_str = "\nOne of the players wants to close the trade.\nEnabled auto-closing on the next selection..."
    pool_fail_str = "\nThe Pool currently seems to have no free slots. Please try again later..."
    quit_trade_str = "\nYou should now quit the current {kind}."
    waiting_synchro_str = "\nWaiting for the other player to be synchronized..."
    arrived_synchro_str = "\nThe other player arrived. Starting party information exchange..."
    transfer_to_hardware_str = "\rSection {index}: {completion}"
    restart_trade_str = "\nStarting a new {kind}."
    incompatible_trade_str = "\nIt looks like the requested trade is not possible.\nYou can't do a synchronous trade with the International version and the Japanese version\nif at least one Pokémon is holding mail.\nEither do a Buffered trade, or remove the mail.\nShutting down..."
    separate_section_str = "\n"
    buffered_negotiation_str = '\nThe other player wants to do a {other_buffered} {kind}.\nWould you like to switch to a {other_buffered} {kind}?'
    buffered_other_negotiation_str = "\nAsking the other player whether they're willing to do a {own_buffered} {kind}..."
    buffered_chosen_str = "\nDecided to do a {own_buffered} {kind}."
    received_buffered_data_str = "\nReceived the {kind} data from the other player!\nYou can now start the real {kind}."
    no_recycle_data_str = "\nBoth players' input is required.\nRestarting the trade from scratch."
    no_move_other_data_str = "\nThe other player's input was not required.\nSkipping receiving their moves data."
    reuse_data_str = "\nReusing the other player's trade data."
    move_other_data_str = "\nThe other player's input was required.\nWaiting for their updated moves data..."
    send_move_other_data_str = "\nSending your updated moves data to the other player."
    no_mail_other_data_str = "\nThe other player's party has no mail.\nSkipping receiving their mail data."
    auto_decline_str = "\nSomething weird was detected with the other player's data.\nAutomatically sending Decline."
    mail_other_data_str = "\nThe other player's party has mail.\nWaiting for them to send it."
    send_mail_other_data_str = "\nSending your mail data to the other player."
    pool_receive_data_str = "\nGetting the Pool's trade offer..."
    pool_recycle_data_str = "\nReusing the previous Pool's trade offer..."
    battle_impossible_verify_opponent_moves_str = "Warning! Temporarily impossible to verify the moves used by the opponent!"
    battle_again_ossible_verify_opponent_moves_str = "It is now possible to verify the moves used by the opponent!"
    battle_synchronous_waiting_opponent_transfer_str = "Waiting for the other player to also start the transfer..."
    battle_wait_press_enter_str = "Waiting {time} seconds before checking for the next user input...\nPress ENTER to skip the wait and instantly start checking for user input."
    battle_reading_user_input_str = "Now reading user input..."
    battle_no_data_str = "Player stopped sending data!\nClosing application!\nIf it is not expected, please report this as an issue!"
    battle_problem_command_other_str = "Issue detected with command sent by other player!\nClosing battle!"
    battle_problem_command_own_str = "Issue detected with command sent by player!\nClosing battle!"
    battle_data_error_initial_str = "ERROR WITH OTHER PLAYER'S DATA!\nSOMETHING CHANGED! ABORTING BATTLE!"
    recap_str = "\nSelected Gen {gen}, {recap_option_selected}, Room {room}\n"
    two_player_trade_long_str = "2 Player Trade"
    two_player_battle_long_str = "2 Player Battle"
    pool_trade_long_str = "Pool Trade"
    two_player_trade_str = "2P"
    two_player_battle_str = "2B"
    pool_trade_str = "PT"
    accepted_str = "Accept"
    decline_str = "Decline"
    yes_no_str = 'Choice (y = Yes, n=No): '
    action_str = "\nInput the action's number: "
    server_str = "Server: "
    port_str = "Port: "
    room_str = "Room (Default = {room}): "
    max_level_str = "New Max Level (Current = {max_level}): "
    battle_change_turn_time_str = "Gen 2 Battle turn time: "
    emulator_host_str = "Emulator's host: "
    emulator_port_str = "Emulator's port: "
    game_selector_menu_str = ("\n=============== Game Selector ===============\n"
                          "1) Red/Blue/Yellow\n"
                          "2) Gold/Silver/Crystal\n"
                          "3) Timecapsule in Gold/Silver/Crystal\n"
                          "4) Special Ruby/Sapphire/Emerald/Fire Red/Leaf Green\n"
                          "m) Multiboot Special Ruby/Sapphire/Emerald/Fire Red/Leaf Green"
                          )
    top_level_menu_str = ("\n=============== Top level Menu ===============\n"
                          "1) Start 2-Player trade (Default)\n"
                          "2) Start Pool trade\n"
                          "b) Start 2-Player battle\n"
                          "3) Options"
                          )
    top_level_menu_gen3_str = ("\n=============== Top level Menu ===============\n"
                          "1) Start 2-Player trade (Default)\n"
                          "2) Start Pool trade\n"
                          "3) Options"
                          )
    options_menu_str = ("\n=============== General Options ===============\n"
                        "0) Exit (Default)\n"
                        "1) Server for connection: {server_host}\n"
                        "2) Port for connection: {server_port}\n"
                        "3) {japanese_str}\n"
                        "4) {sanity_checks_str}\n"
                        "5) Change Verbosity (Current: {verbose})\n"
                        "\n=============== 2-Player trade/battle Options ===============\n"
                        "6) Change to {other_buffered} Trading/Battle (Current: {own_buffered})\n"
                        "7) {kill_on_byte_drops_str}\n"
                        "{battle_turn_time_str}"
                        "\n=============== Pools trade Options ===============\n"
                        "8) Set Max Level (Current: {max_level})"
                        "{gen_2_eggify_str}"
                        "{emulator_str}"
                        )
    gen_2_eggify_str = ("\n9) {egg_str}")
    battle_turn_time_option_str = ("btt) Time between turns: {battle_turn_time}\n")
    emulator_options_str = ("\n\n=============== Emulator Options ===============\n"
                            "10) Host for emulator connection: {emulator_host}\n"
                            "11) Port for emulator connection: {emulator_port}"
                            )
    
    def int_to_three_str(integer):
        ret = ""
        if integer < 100:
            ret += " "
        if integer < 10:
            ret += " "
        ret += str(integer)
        return ret
    
    def x_out_of_y_str(x, y):
        return GSCTradingStrings.int_to_three_str(x) + "/" + GSCTradingStrings.int_to_three_str(y)

    def get_accepted_str(is_decline):
        if is_decline:
            return GSCTradingStrings.decline_str
        return GSCTradingStrings.accepted_str

    def get_buffered_str(buffered):
        if buffered:
            return GSCTradingStrings.buffered_str
        return GSCTradingStrings.synchronous_str

    def get_kind_str(is_battle):
        if is_battle:
            return GSCTradingStrings.kind_battle_str
        return GSCTradingStrings.kind_trade_str

    def get_kind_ing_str(is_battle):
        if is_battle:
            return GSCTradingStrings.kind_battle_str
        return GSCTradingStrings.kind_trade_str

    def get_recap_option_selected(menu):
        if menu.is_battle:
            return GSCTradingStrings.two_player_battle_long_str
        if menu.trade_type == GSCTradingStrings.two_player_trade_str:
            return GSCTradingStrings.two_player_trade_long_str
        if menu.trade_type == GSCTradingStrings.pool_trade_str:
            return GSCTradingStrings.pool_trade_long_str
        return "?????"
    
    def buffered_negotiation_print(buffered, is_battle):
        print(GSCTradingStrings.buffered_negotiation_str.format(other_buffered=GSCTradingStrings.get_buffered_str(not buffered), kind=GSCTradingStrings.get_kind_str(is_battle)))
        print(GSCTradingStrings.yes_no_str, end = '')
    
    def version_print(major, minor, build):
        print(GSCTradingStrings.version_str.format(major=major, minor=minor, build=build))
    
    def buffered_other_negotiation_print(buffered, is_battle):
        print(GSCTradingStrings.buffered_other_negotiation_str.format(own_buffered = GSCTradingStrings.get_buffered_str(buffered), kind=GSCTradingStrings.get_kind_str(is_battle)))
    
    def chosen_buffered_print(buffered, is_battle):
        print(GSCTradingStrings.buffered_chosen_str.format(own_buffered = GSCTradingStrings.get_buffered_str(buffered), kind=GSCTradingStrings.get_kind_str(is_battle)))
        if buffered:
            print(GSCTradingStrings.buffered_sit_table_str.format(kind_ing=GSCTradingStrings.get_kind_ing_str(is_battle)))
            
    def game_selector_menu_print():
        print(GSCTradingStrings.game_selector_menu_str)
            
    def top_menu_print(gen, is_timecapsule):
        if (gen == 3) or is_timecapsule:
            print(GSCTradingStrings.top_level_menu_gen3_str)
            return
        print(GSCTradingStrings.top_level_menu_str)
    
    def get_japanese_str(japanese):
        if japanese:
            return GSCTradingStrings.unset_japanese_str
        return GSCTradingStrings.set_japanese_str
    
    def get_sanity_checks_str(sanity_checks):
        if sanity_checks:
            return GSCTradingStrings.active_sanity_checks_str
        return GSCTradingStrings.inactive_sanity_checks_str
    
    def get_kill_on_byte_drops_str(kill_on_byte_drops):
        if kill_on_byte_drops:
            return GSCTradingStrings.active_kill_on_byte_drops_str
        return GSCTradingStrings.inactive_kill_on_byte_drops_str
    
    def get_eggify_str(options):
        if not options.gen == 2:
            return ""
        egg_str = GSCTradingStrings.set_egg_str
        if options.egg:
            egg_str = GSCTradingStrings.unset_egg_str
        return GSCTradingStrings.gen_2_eggify_str.format(egg_str=egg_str)

    def get_battle_turn_time_option_str(options):
        if not options.gen == 2:
            return ""
        return GSCTradingStrings.battle_turn_time_option_str.format(battle_turn_time=options.time_between_battle_turns)
    
    def get_emulator_str(options):
        if not options.is_emulator:
            return ""
        return GSCTradingStrings.emulator_options_str.format(emulator_host=options.emulator[0], emulator_port=options.emulator[1])
        
    def options_menu_print(options):
        print(GSCTradingStrings.options_menu_str.format(server_host=options.server[0], server_port=options.server[1],
                                                     japanese_str=GSCTradingStrings.get_japanese_str(options.japanese),
                                                     sanity_checks_str=GSCTradingStrings.get_sanity_checks_str(options.do_sanity_checks),
                                                     verbose=options.verbose,
                                                     other_buffered=GSCTradingStrings.get_buffered_str(not options.buffered),
                                                     own_buffered=GSCTradingStrings.get_buffered_str(options.buffered),
                                                     kill_on_byte_drops_str=GSCTradingStrings.get_kill_on_byte_drops_str(options.kill_on_byte_drops),
                                                     emulator_str = GSCTradingStrings.get_emulator_str(options),
                                                     max_level = options.max_level,
                                                     gen_2_eggify_str = GSCTradingStrings.get_eggify_str(options),
                                                     battle_turn_time_str = GSCTradingStrings.get_battle_turn_time_option_str(options)
                                                     )
             )

    def choice_print():
        print(GSCTradingStrings.action_str, end='')
    
    def change_server_print():
        print(GSCTradingStrings.server_str, end='')
    
    def change_port_print():
        print(GSCTradingStrings.port_str, end='')
    
    def change_max_level_print(max_level):
        print(GSCTradingStrings.max_level_str.format(max_level=max_level), end='')
    
    def change_room_print(room):
        print(GSCTradingStrings.room_str.format(room=room), end='')
    
    def change_battle_turn_time_print():
        print(GSCTradingStrings.battle_change_turn_time_str, end='')
    
    def change_emu_server_print():
        print(GSCTradingStrings.emulator_host_str, end='')
    
    def change_emu_port_print():
        print(GSCTradingStrings.emulator_port_str, end='')
