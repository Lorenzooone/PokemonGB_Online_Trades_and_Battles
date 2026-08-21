from .gsc_battling import GSCBattling
from .gsc_trading_data_utils import GSCUtilsLoaders, GSCUtilsMisc

class GSCBattlingJP(GSCBattling):
    """
    Class which handles the battling process for the player.
    """
    next_section = 0xFD
    no_input = 0xFE
    end_of_line = 0x50
    single_text_len = 0xB
    # Positions off by one so the last one is covered by the
    # checks for EOL
    end_of_player_name_pos = 5
    end_of_gsc_data_pos = 0x13A
    player_name_len_diff = 5
    pokemon_name_len_diff = 5
    fillers = [{}, {
        end_of_player_name_pos: [player_name_len_diff, end_of_line],
        end_of_gsc_data_pos + (single_text_len * 0): [player_name_len_diff, end_of_line],
        end_of_gsc_data_pos + (single_text_len * 1): [player_name_len_diff, end_of_line],
        end_of_gsc_data_pos + (single_text_len * 2): [player_name_len_diff, end_of_line],
        end_of_gsc_data_pos + (single_text_len * 3): [player_name_len_diff, end_of_line],
        end_of_gsc_data_pos + (single_text_len * 4): [player_name_len_diff, end_of_line],
        end_of_gsc_data_pos + (single_text_len * 5): [player_name_len_diff, end_of_line],
        end_of_gsc_data_pos + (single_text_len * 6): [pokemon_name_len_diff, end_of_line],
        end_of_gsc_data_pos + (single_text_len * 7): [pokemon_name_len_diff, end_of_line],
        end_of_gsc_data_pos + (single_text_len * 8): [pokemon_name_len_diff, end_of_line],
        end_of_gsc_data_pos + (single_text_len * 9): [pokemon_name_len_diff, end_of_line],
        end_of_gsc_data_pos + (single_text_len * 10): [pokemon_name_len_diff, end_of_line],
        end_of_gsc_data_pos + (single_text_len * 11): [pokemon_name_len_diff, end_of_line]
    }, {}, {}, {}]
    drop_bytes_checks = [[0xA, 0x1B9, 0xC5], [next_section, next_section, no_input], [0,4,0]]
    
    def __init__(self, sending_func, receiving_func, connection, menu, kill_function, pre_sleep):
        super(GSCBattlingJP, self).__init__(sending_func, receiving_func, connection, menu, kill_function, pre_sleep)
