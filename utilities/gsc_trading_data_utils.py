import math
import sys
import types
from .gsc_trading_strings import GSCTradingStrings

debug_print_if_file_is_missing = False

class GSCUtilsLoaders:
    """
    Class which contains methods used to load structures from
    binary or text files.
    """

    def prepare_dict(target):
        lines = GSCUtilsLoaders.read_text_file(target)
        dict = {}
        for i in lines:
            dict[i.split()[0]] = int(i.split()[1])
        return dict

    def prepare_exp_lists(lines):
        exp_lists = [[], [], [], [], [], []]
        for i in range(GSCUtils.max_level):
            columns = lines[i].split()
            for j in range(6):
                exp_lists[j] += [int(columns[j])]
        return exp_lists
    
    def read_text_file(target):
        try:
            with open(target,"r", encoding="utf-8") as f:
                lines=f.readlines()
        except FileNotFoundError as e:
            return []
        return lines
    
    def prepare_learnsets(data):
        dict = {}
        entries = data[0]
        for i in range(entries):
            pos = GSCUtilsMisc.read_short(data, 1 + (i * 2))
            entry = {}
            species = data[pos]
            levels = data[pos+1]
            pos += 2
            for j in range(levels):
                level = data[pos]
                num_moves = data[pos+1]
                moves_list = []
                pos += 2
                for k in range(num_moves):
                    moves_list += [data[pos]]
                    pos += 1
                entry[level] = moves_list
            dict[species] = entry
        return dict

    def prepare_check_list(data):
        ret = [False] * 0x100
        if data is not None:
            for i in data:
                ret[i] = True
        return ret
    
    def prepare_evolution_check_list(data):
        ret = [(False, None, None)] * 0x100
        
        if data is not None:
            data_len = int(len(data)/3)
            for i in range(data_len):
                ret[data[i]] = (True, None, data[i + (2*data_len)])
                if data[i + data_len] != 0:
                    ret[data[i]] = (True, data[i + data_len], data[i + (2*data_len)])
        return ret

    def prepare_stats(data, num_stats, num_entries):
        ret = [0] * num_entries
        for i in range(num_entries):
            ret[i] = data[(i)*num_stats:(i+1)*num_stats]
        return ret

    def prepare_functions_map(data, functions):
        call_map = [None] * len(data)
        for i in range(len(data)):
            call_map[i] = functions[data[i]]
        return call_map

    def load_trading_data(target, lengths):
        data = None
        try:
            with open(target, 'rb') as newFile:
                data = GSCUtilsMisc.divide_data(list(newFile.read(sum(lengths))), lengths)
        except FileNotFoundError as e:
            pass
        return data

    def load_replacement_data_double_dict(data, data_len = 1):
        out_forward = dict()
        out_backwards = dict()
        
        entry_len = data_len * 2
        for i in range(len(data) // entry_len):
            entry_pos = i * entry_len
            elem_one = GSCUtilsMisc.from_n_bytes_le(data, data_len, entry_pos)
            elem_two = GSCUtilsMisc.from_n_bytes_le(data, data_len, entry_pos + data_len)
            out_forward[elem_one] = elem_two
            out_backwards[elem_two] = elem_one
        return out_forward, out_backwards

class GSCUtils:
    """
    Class which contains generic methods and data used for
    pokémon-related functions.
    """
    base_folder = "useful_data/gsc/"
    evolution_ids_path = "evolution_ids.bin"
    mail_ids_path = "ids_mail.bin"
    no_mail_path = "no_mail_section.bin"
    no_mail_old_path = "no_mail_section_old.bin"
    base_random_path = "base_random_section.bin"
    base_stats_path = "stats.bin"
    moves_pp_list_path = "moves_pp_list.bin"
    learnset_evos_path = "learnset_evos.bin"
    exp_groups_path = "pokemon_exp_groups.bin"
    exp_lists_path = "pokemon_exp.txt"
    bad_ids_and_replacement_text_special_kor_path = "bad_ids_and_replacement_text_special_kor.bin"
    bad_ids_text_full_kor_path = "bad_ids_text_full_kor.bin"
    
    everstone_id = 0x70
    egg_id = 0xFD
    end_of_line = 0x50
    num_entries = 0x100
    name_size = 0xB
    hp_stat_id = 0
    stat_id_base_conv_table = [0,1,2,5,3,4]
    stat_id_iv_conv_table = [0,0,1,2,3,3]
    stat_id_exp_conv_table = [0,1,2,3,4,4]
    patch_set_base_pos = [0x13, 0x186, 0, 0xC6] #[0x13, 0xC6, 0]
    patch_set_start_info_pos = [7, 0x1DA, 0xFC, 0x11A] #[7, 0x11A, 0xFC]
    egg_value = 0x38
    min_level = 2
    max_level = 100
    num_stats = 6

    korean_language_2_bytes_special_language = 0x1F # Last bit in 32 bits
    korean_special_replacement = 0x6B
    korean_patched_special_replacement = 0x6C
    num_valid_user_input_tables = 0xC
    eol_user_input_table_value = 0xC
    jpn_name_len = 5
    start_valid_user_input_tables_byte = (0x100 - (num_valid_user_input_tables * num_valid_user_input_tables))
    prohibited_char = 0xFE
    prohibited_char_replacement = 0x2D
    
    evolution_ids = None
    mail_ids = None
    base_stats = None
    no_mail_section = None
    no_mail_section_old = None
    moves_pp_list = None
    learnsets = None
    exp_groups = None
    exp_lists = None
    
    def __init__(self):
        curr_class = type(self)
        curr_class.evolution_ids = GSCUtilsLoaders.prepare_evolution_check_list(GSCUtilsMisc.read_data(self.get_path(curr_class.evolution_ids_path)))
        curr_class.mail_ids = GSCUtilsLoaders.prepare_check_list(GSCUtilsMisc.read_data(self.get_path(curr_class.mail_ids_path)))
        curr_class.no_mail_section = GSCUtilsMisc.read_data(self.get_path(curr_class.no_mail_path))
        curr_class.no_mail_section_old = GSCUtilsMisc.read_data(self.get_path(curr_class.no_mail_old_path))
        curr_class.base_random_section = GSCUtilsMisc.read_data(self.get_path(curr_class.base_random_path))
        curr_class.base_stats = GSCUtilsLoaders.prepare_stats(GSCUtilsMisc.read_data(self.get_path(curr_class.base_stats_path)), curr_class.num_stats, curr_class.num_entries)
        curr_class.moves_pp_list = GSCUtilsMisc.read_data(self.get_path(curr_class.moves_pp_list_path))
        curr_class.learnsets = GSCUtilsLoaders.prepare_learnsets(GSCUtilsMisc.read_data(self.get_path(curr_class.learnset_evos_path)))
        curr_class.exp_groups = GSCUtilsMisc.read_data(self.get_path(curr_class.exp_groups_path))
        curr_class.exp_lists = GSCUtilsLoaders.prepare_exp_lists(GSCUtilsLoaders.read_text_file(self.get_path(curr_class.exp_lists_path)))
        curr_class.bad_ids_text_special_to_kor, curr_class.bad_ids_text_special_from_kor = GSCUtilsLoaders.load_replacement_data_double_dict(GSCUtilsMisc.read_data(self.get_path(curr_class.bad_ids_and_replacement_text_special_kor_path)))
        curr_class.bad_ids_text_kor_full_list = (GSCUtilsMisc.read_data(self.get_path(curr_class.bad_ids_text_full_kor_path)))
    
    def get_path(self, target):
        return self.base_folder + target
    
    def get_level_exp(species, exp, utils_class):
        start = utils_class.min_level
        end = utils_class.max_level
        if exp < utils_class.get_exp_level(species, start + 1, utils_class):
            return start
        if exp >= utils_class.get_exp_level(species, end, utils_class):
            return end
        end_search = False
        while not end_search:
            check_level = math.floor((start+end)/2)
            level_exp = utils_class.get_exp_level(species, check_level, utils_class)
            next_level_exp = utils_class.get_exp_level(species, check_level + 1, utils_class)
            if exp < level_exp:
                end = check_level
            elif exp > next_level_exp:
                start = check_level
            elif exp == next_level_exp:
                return check_level + 1
            else:
                return check_level
        return utils_class.max_level
    
    def get_exp_level(species, level, utils_class):
        return utils_class.exp_lists[utils_class.exp_groups[species]][level-1]
    
    def final_stat_calc_step(stat_id, level, utils_class):
        if stat_id != utils_class.hp_stat_id:
            return 5
        return level + 10
    
    def get_iv(iv, stat_id, utils_class):
        if stat_id != utils_class.hp_stat_id:
            return iv[utils_class.stat_id_iv_conv_table[stat_id]]
        return ((iv[0]&1)<<3) | ((iv[1]&1)<<2) | ((iv[2]&1)<<1) | (iv[3]&1)
    
    def get_exp(stat_exp, stat_id, utils_class):
        return stat_exp[utils_class.stat_id_exp_conv_table[stat_id]]
    
    def get_base_stat(species, stat_id, utils_class):
        return utils_class.base_stats[species][utils_class.stat_id_base_conv_table[stat_id]]

    def get_stat_exp_contribution(stat_exp):
        val = math.ceil(math.sqrt(stat_exp))
        if val >= 0x100:
            val = 0xFF
        return math.floor(val / 4)
    
    def stat_calculation(stat_id, species, ivs, stat_exp, level, utils_class, do_exp=True):
        inter_value = (utils_class.get_base_stat(species, stat_id, utils_class) + utils_class.get_iv(ivs, stat_id, utils_class)) * 2
        if do_exp:
            inter_value += utils_class.get_stat_exp_contribution(utils_class.get_exp(stat_exp, stat_id, utils_class))
        inter_value = math.floor((inter_value*level)/100)
        return inter_value + utils_class.final_stat_calc_step(stat_id, level, utils_class)
    
    def is_item_mail(item):
        return GSCUtilsMisc.check_normal_list(GSCUtils.mail_ids, item)
    
    def is_evolving(species, item):
        if species >= 0x100 or species < 0:
            return False
        evo_info = GSCUtils.evolution_ids[species]
        if evo_info[0]:
            if item != GSCUtils.everstone_id:
                if (evo_info[1] is None) or (item == evo_info[1]):
                    return True
        return False
    
    def get_evolution(species, item):
        if not GSCUtils.is_evolving(species, item):
            return None
        return GSCUtils.evolution_ids[species][2]
    
    def get_evolution_item(species):
        return GSCUtils.evolution_ids[species][1]
    
    def get_patch_set_num_index(is_mail, is_japanese, is_old_mail_data):
        patch_sets_num = 2
        patch_sets_index = 0
        if is_mail:
            patch_sets_num = 1
            patch_sets_index = 1
            if is_old_mail_data:
                patch_sets_index = 3
            # Japanese does not have a "New" mail form...
            # So just replace it regardless...
            if is_japanese:
                patch_sets_index = 2
        return patch_sets_num, patch_sets_index
    
    def apply_patches(data, patch_set, utils_class, is_mail=False, is_japanese=False, is_old_mail_data = False):
        """
        Applies patch data (turns the previously read data into 0xFE)
        """
        patch_sets_num, patch_sets_index = utils_class.get_patch_set_num_index(is_mail, is_japanese, is_old_mail_data)
        
        base = utils_class.patch_set_base_pos[patch_sets_index]
        start = utils_class.patch_set_start_info_pos[patch_sets_index]
        i = 0
        while (patch_sets_num > 0) and ((start+i) < len(patch_set)):
            read_pos = patch_set[start+i]
            i += 1
            if read_pos == 0xFF:
                patch_sets_num -= 1
                base += 0xFC
            elif read_pos > 0 and (read_pos+base) < len(data):
                data[read_pos+base-1] = 0xFE

    def create_patches_data(data, patch_set, utils_class, is_mail=False, is_japanese=False, is_old_mail_data = False):
        """
        Creates patch data (turns 0xFE into a patch offset)
        """
        patch_sets_num, patch_sets_index = utils_class.get_patch_set_num_index(is_mail, is_japanese, is_old_mail_data)
        
        base = utils_class.patch_set_base_pos[patch_sets_index]
        start = utils_class.patch_set_start_info_pos[patch_sets_index]
        i = 0
        j = 0
        while (patch_sets_num > 0) and ((start+i) < len(patch_set)) and ((base+j) < len(data)):
            read_data = data[base+j]
            if read_data == 0xFE:
                data[base+j] = 0xFF
                patch_set[start+i] = j+1
                i+=1
            j += 1
            if j == 0xFC:
                base += 0xFC
                j = 0
                patch_set[start+i] = 0xFF
                i+=1
                patch_sets_num -= 1
                
        if j != 0:
            if (start+i) >= len(patch_set):
                i = len(patch_set)-start-1
            patch_set[start+i] = 0xFF
            i+=1

    def convert_language_int_to_list(languages_int):
        ret_val = []
        index = 0

        while languages_int != 0:
            if languages_int & (1 << index):
                languages_int &= ~(1 << index)
                if index != GSCUtils.korean_language_2_bytes_special_language:
                    ret_val += [index]
            index += 1
        return ret_val

    def convert_language_list_to_int(languages_list, mon_data, gen):
        from .text_conversions import PokemonNamesForGen, PokemonTextConversions
        ret_val = 0
        mon = mon_data[0]

        languages_list = list(languages_list)
        if len(languages_list) <= 0:
            return ret_val

        for language in languages_list:
            language_bit = 1 << language
            ret_val |= language_bit
            if language == PokemonNamesForGen.KOREAN_LANGUAGE:
                out_value, is_partial, is_question_mark = PokemonTextConversions.convert_genx_char_to_char(mon.nickname.values[0], gen, language)
                if is_partial:
                    out_value, is_partial, is_question_mark = PokemonTextConversions.convert_genx_char_to_char(mon.ot_name.values[0], gen, language)
                if is_partial:
                    language_bit = 1 << GSCUtils.korean_language_2_bytes_special_language
                    ret_val |= language_bit
        return ret_val

    def single_mon_from_data_multilanguage(checks, data):
        from .text_conversions import PokemonNamesForGen
        language_valid_list = []
        language_match_list = []
        language_ret_data_dict = dict()
        gen = 2

        for language in PokemonNamesForGen.all_languages_list:
            non_checked = GSCTradingPokémonInfo.set_data(data)
            non_checked.apply_all_text_transforms_to_all(language)

            checks.language = language
            ret_data = GSCUtils.single_mon_from_data(checks, data)

            if ret_data is None:
                continue
            
            language_ret_data_dict[language] = ret_data

            if ret_data[0].nickname.get_length() > PokemonNamesForGen.get_pokemon_max_nickname_length(gen, language):
                continue

            if ret_data[0].ot_name.get_length() > PokemonNamesForGen.get_trainer_max_name_length(gen, language):
                continue

            if ret_data[0].is_text_equal(non_checked, do_mail = False):
                language_match_list += [language]

        if len(language_ret_data_dict.keys()) <= 0:
            return None

        language_ref_list = language_match_list
        if len(language_match_list) <= 0:
            language_ref_list = list(language_ret_data_dict.keys())
        mon_data_out = language_ret_data_dict[language_ref_list[0]]

        #print(mon_data_out[0].get_data())
        #print(non_checked.get_data())
        #print(language_ref_list)
        return mon_data_out + [GSCUtils.convert_language_list_to_int(language_ref_list, mon_data_out, gen)]
    
    def single_mon_from_data(checks, data):
        ret = None
        
        # Prepare sanity checks stuff
        checks.reset_species_item_list()
        checks.set_single_team_size()
        checks.reset_text_buffers()
        checks.prepare_patch_sets_buffer()
        checks.prepare_species_buffer()
        checker = checks.single_pokemon_checks_map
        has_new_mail_data = True
        if len(data) <= len(checker):
            checker = checks.single_pokemon_checks_map_old
            has_new_mail_data = False
        
        if len(data) > len(checker):
            # Prepares the pokémon data. For the raw one
            raw = GSCTradingPokémonInfo.set_data(data, is_new_mail_data = has_new_mail_data)

            # Handle getting/sending eggs. That requires one extra byte
            is_egg = False
            if data[len(checker)] == GSCUtils.egg_value:
                is_egg = True
            
            # Prepare for further checks
            if is_egg:
                checks.species_cleaner(GSCUtils.egg_id)
            else:
                checks.species_cleaner(data[0])
            checks.prepare_species_buffer()

            # Account for mail shenanigans
            if raw.has_mail():
                from .text_conversions import PokemonNamesForGen
                # Avoid patching a new newline and end of line in a converted korean mail...
                if raw.mail.get_mail_language() == PokemonNamesForGen.KOREAN_LANGUAGE:
                    checks.do_mail_newline_checks = False
                
            # Applies the checks to the received data.
            # If the sanity checks are off, this will be a simple copy
            purified_data = checks.apply_checks_to_data(checker, data)
                
            # Prepares the pokémon data. For the cleaned one
            mon = GSCTradingPokémonInfo.set_data(purified_data, is_new_mail_data = has_new_mail_data)
            
            # If the sanity checks are on, has the pokémon changed
            # too much from the cleaning?
            if not mon.has_changed_significantly(raw):
                ret = [mon, is_egg]
        return ret
    
    def single_mon_to_data(mon, is_egg, use_new_mail_data = True):
        egg_val = 0
        if is_egg:
            egg_val = GSCUtils.egg_value
        return mon.get_data(is_new_mail_data = use_new_mail_data) + [egg_val]

    def process_from_korean_special_table_value(in_data, utils_class, is_first_nybble):
        table_value = 0
        if is_first_nybble:
            table_value = ((in_data - utils_class.start_valid_user_input_tables_byte) % utils_class.num_valid_user_input_tables) + 1
        else:
            table_value = ((in_data - utils_class.start_valid_user_input_tables_byte) // utils_class.num_valid_user_input_tables) + 1
        if table_value == utils_class.eol_user_input_table_value:
            table_value = utils_class.end_of_line
        if in_data == utils_class.end_of_line:
            table_value = utils_class.end_of_line
        return table_value

    def apply_text_transform_protect_international_from_korean_special(utils_class, in_char_list, processing_obj):
        if len(in_char_list) == 1:
            return [in_char_list[0] & 0xF]
        if len(in_char_list) == 2:
            corr_mask = (in_char_list[0] << 3) & 0x80
            return [in_char_list[1] & (~corr_mask)]
        if len(in_char_list) == 3:
            return [utils_class.process_from_korean_special_table_value(in_char_list[2], utils_class, True)]
        if len(in_char_list) == 4:
            corr_mask = (in_char_list[0] << 2) & 0x80
            return [in_char_list[3] & (~corr_mask)]
        if len(in_char_list) == 5:
            return [utils_class.process_from_korean_special_table_value(in_char_list[2], utils_class, False)]
        if len(in_char_list) == 6:
            # Are we encountering a Japanese-truncated Korean name?
            if (in_char_list[5] == utils_class.end_of_line) and (not processing_obj.has_encountered_eol):
                # If yes, force the next one to be EOL.
                # Technically it will be EOL due to the extra bytes regardless,
                # but might as well be sure.
                processing_obj.is_korean_special_was_japanese_truncated = True
                return [0xF0]
            processing_obj.is_korean_special_was_japanese_truncated = False
            return [in_char_list[5]]
        if len(in_char_list) == 7:
            if processing_obj.is_korean_special_was_japanese_truncated:
                return [utils_class.end_of_line]
            return [utils_class.process_from_korean_special_table_value(in_char_list[6], utils_class, True)]
        if len(in_char_list) == 8:
            return [in_char_list[7]]
        if len(in_char_list) == 9:
            # Add back the missing byte from the start
            return [utils_class.process_from_korean_special_table_value(in_char_list[6], utils_class, False), in_char_list[8]]
        return [in_char_list[-1]]

    def apply_text_transform_protect_korean_from_jpn_special(utils_class, in_char_list):
        if len(in_char_list) == 1:
            return []
        if (len(in_char_list) >= 2) and (len(in_char_list) < (2 + utils_class.jpn_name_len)):
            index = len(in_char_list) - 2
            corr_mask = (in_char_list[0] << (7 - index)) & 0x80
            out_value = [in_char_list[1 + index] & (~corr_mask)]
            if index == (utils_class.jpn_name_len - 1):
                # Add back the missing two bytes from the start
                out_value += [utils_class.end_of_line, utils_class.end_of_line]
            return out_value
        return [in_char_list[-1]]

    def replace_fe_in_patched_out_data(utils_class, text_entry):
        for i in range(len(text_entry.values)):
            if text_entry.values[i] == utils_class.prohibited_char:
                text_entry.values[i] = utils_class.prohibited_char_replacement

    def patch_out_bad_chars_protect_international_from_korean_buffered_only(utils_class, text_entry):
        if text_entry.values[0] == utils_class.korean_special_replacement:
            # Pre-applied
            return

        #print("PATCHING KOR FOR INT AND JPN")
        #print(text_entry.values)
        first_bytes = []
        second_bytes = []
        corr_bits = []
        # Split the data...
        for i in range(5):
            first_bytes += [text_entry.values[(i * 2)]]
            if first_bytes[i] == utils_class.end_of_line:
                first_bytes[i] = utils_class.eol_user_input_table_value
            if first_bytes[i] > utils_class.num_valid_user_input_tables:
                first_bytes[i] = utils_class.eol_user_input_table_value - 1
            if i != 0:
                first_bytes[i] -= 1
            second_bytes += [text_entry.values[(i * 2) + 1]]
            if (second_bytes[i] < 0x60) and (second_bytes[i] != utils_class.end_of_line):
                corr_bits += [1]
            else:
                corr_bits += [0]

        # Preprocess second_bytes[0,1]
        if corr_bits[0] != 0:
            second_bytes[0] |= 0x80
        if corr_bits[1] != 0:
            second_bytes[1] |= 0x80

        # Now re-insert it...
        text_entry.values[0] = utils_class.korean_special_replacement
        text_entry.values[1] = first_bytes[0] | (corr_bits[0] << 4) | (corr_bits[1] << 5) | 0x80
        text_entry.values[2] = second_bytes[0]
        text_entry.values[3] = utils_class.start_valid_user_input_tables_byte + first_bytes[1] + (first_bytes[2] * utils_class.num_valid_user_input_tables)
        text_entry.values[4] = second_bytes[1]
        text_entry.values[5] = utils_class.end_of_line
        text_entry.values[6] = second_bytes[2]
        text_entry.values[7] = utils_class.start_valid_user_input_tables_byte + first_bytes[3] + (first_bytes[4] * utils_class.num_valid_user_input_tables)
        text_entry.values[8] = second_bytes[3]
        text_entry.values[9] = second_bytes[4]

        # End it all by replacing FEs
        utils_class.replace_fe_in_patched_out_data(utils_class, text_entry)

    def patch_out_bad_chars_protect_korean_from_jpn_buffered_only(utils_class, text_entry):
        # While patching these chars could be done even during synchronous
        # trades, we can only do it in buffered trades due to the need to
        # get the language of the name beforehand to confirm that patching
        # should be done...

        if text_entry.values[0] == utils_class.korean_patched_special_replacement:
            # Pre-applied
            return

        has_bad_chars = False
        bad_chars_list = []
        for i in range (len(text_entry.values)):
            if text_entry.values[i] == utils_class.end_of_line:
                break
            if text_entry.values[i] in utils_class.bad_ids_text_kor_full_list:
                has_bad_chars = True
                bad_chars_list += [1]
            else:
                bad_chars_list += [0]
        if not has_bad_chars:
            return

        #print("PATCHING JPN FOR KOR")
        #print(text_entry.values)
        # We have confirmed that bad characters for Korean are present...
        # Now patch them out...
        # We could patch them before, but I'd like the steps to be separate.
        temp_values = text_entry.values[:]
        corr_bit_value = 0
        for i in range(len(bad_chars_list)):
            corr_bit_value |= bad_chars_list[i] << i
            if bad_chars_list[i] == 1:
                temp_values[i] |= 0x80

        text_entry.values[0] = utils_class.korean_patched_special_replacement
        text_entry.values[1] = corr_bit_value | 0x80
        for i in range(len(bad_chars_list)):
            text_entry.values[2 + i] = temp_values[i]
        for i in range(2 + len(bad_chars_list), len(text_entry.values)):
            text_entry.values[i] = utils_class.end_of_line

        # End it all by replacing FEs
        utils_class.replace_fe_in_patched_out_data(utils_class, text_entry)

    def get_general_string_ready_for_counting_lines_and_chars(target_str):
        lines_to_process = target_str.split("\n")
        processed_lines = []
        for i in range(len(lines_to_process)):
            line = lines_to_process[i]
            line_interruptions = line.replace("<", ">").split(">")
            final_line = ""
            # Basically, replace characters within <> with a 1 for counting
            for i in range(len(line_interruptions)):
                if (i % 2) == 0:
                    final_line += line_interruptions[i]
                else:
                    final_line += "1"
            processed_lines += [final_line]
        return processed_lines

    def get_basic_checks():
        return GSCChecks([0,0,0], True, use_strict_language_checks = True)

class GSCUtilsMisc:
    """
    Class which contains generic methods and data used for
    general functions.
    """

    def read_data(target):
        data = None
        try:
            with open(target, 'rb') as newFile:
                tmpdata = list(newFile.read())
                data = tmpdata
        except FileNotFoundError as e:
            if debug_print_if_file_is_missing:
                print("File not found: " + str(target))
        return data

    def write_data(target, data):
        try:
            with open(target, 'wb') as newFile:
                newFile.write(bytearray(data))
        except IOError as e:
           print(GSCTradingStrings.io_error_str.format(e.errno, e.strerror))
        except: #handle other exceptions such as attribute errors
           print(GSCTradingStrings.unknown_error_str, sys.exc_info()[0])
    
    def read_nybbles(val):
        return [(val&0xF0) >> 4, val & 0xF]
    
    def read_short_le(data, pos):
        return ((data[pos]) + (data[pos+1]<<8))
    
    def read_int_le(data, pos):
        return (data[pos]) + (data[pos+1]<<8) + (data[pos+2]<<16) + (data[pos+3]<<24)
    
    def read_short(data, pos):
        return ((data[pos] << 8) + (data[pos+1]))
    
    def write_short(data, pos, short_data):
        data[pos] = (short_data >> 8) & 0xFF
        data[pos+1] = short_data & 0xFF
    
    def write_int_le(data, pos, int_data):
        data[pos] = int_data & 0xFF
        data[pos+1] = (int_data >> 8) & 0xFF
        data[pos+2] = (int_data >> 16) & 0xFF
        data[pos+3] = (int_data >> 24) & 0xFF
    
    def write_short_le(data, pos, short_data):
        data[pos] = short_data & 0xFF
        data[pos+1] = (short_data >> 8) & 0xFF

    def write_int_le_to_buffer(int_data):
        data = []
        for _ in range(4):
            data += [0]
        GSCUtilsMisc.write_int_le(data, 0, int_data)
        return data

    def write_short_le_to_buffer(short_data):
        data = []
        for _ in range(2):
            data += [0]
        GSCUtilsMisc.write_short_le(data, 0, short_data)
        return data
    
    def to_n_bytes_le(in_data, n_bytes):
        data = [0] * n_bytes
        for i in range(n_bytes):
            data[i] = (in_data>>(8*i)) & 0xFF
        return data

    def from_n_bytes_le(data, n_bytes, start = 0):
        out_data = 0
        for i in range(n_bytes):
            out_data |= data[start + i]<<(8*i)
        return out_data

    def inc_byte(val):
        val += 1
        if val >= 256:
            val = 0
        return val
    
    def copy_to_data(data, pos, values, length=None):
        if length is None:
            length = len(values)
        data[pos:pos+length] = values[:length]
        
    def check_normal_list(checking_list, value):
        if value >= 0x100 or value < 0:
            return False
        return checking_list[value]
    
    def divide_data(data, lengths):
        div_data = []
        total_lengths = GSCUtilsMisc.calc_divide_lengths(lengths)
        for i in range(len(lengths)):
            div_data += [data[total_lengths[i]:total_lengths[i+1]]]
        return div_data
    
    def calc_divide_lengths(lengths):
        total_lengths = []
        curr_len = 0
        for i in range(len(lengths)):
            total_lengths += [curr_len]
            curr_len += lengths[i]
        total_lengths += [curr_len]
        return total_lengths
        
    def default_if_none(data, default_data):
        if data is not None:
            return data
        return default_data

    def print_table_hex(data, num_elems_per_column = 16):
        if data is None:
            return
        print("{")
        num_elems = len(data)
        num_rows = (num_elems + num_elems_per_column - 1) // num_elems_per_column
        for i in range(num_rows):
            for j in range(num_elems_per_column):
                wanted_elem = (i * num_elems_per_column) + j
                if wanted_elem < len(data):
                    print("{0:02x} ".format(data[wanted_elem]), end='')
            print()
        print("}")
    
    def verbose_print(to_print, verbose, end='\n'):
        if verbose:
            print(to_print, end=end)

class GSCTradingText:
    """
    Class which contains a text entry from the trading data.
    """

    def __init__(self, data, start, length=0xB, data_start=0):
        self.values = data[start:start+length]
        self.start_at = data_start
        self.utils_class = self.get_utils_class()
    
    def get_utils_class(self):
        return GSCUtils
    
    def values_equal(self, other):
        """
        :param other: Bytes, to be compared to the ones from its own values.
        """
        for i in range(len(self.values)):
            if self.values[i] == self.utils_class.end_of_line and (i >= len(other) or other[i] == self.utils_class.end_of_line):
                return True
            if i >= len(other):
                return False
            if self.values[i] != other[i]:
                return False
        if len(other) == len(self.values) or other[len(self.values)] == self.utils_class.end_of_line:
            return True
        return False

    def get_length(self):
        for i in range(len(self.values) - self.start_at):
            if self.values[i] == self.utils_class.end_of_line:
                return i - self.start_at
        return len(self.values) - self.start_at

    def create_from_string(string, length=0xB):
        from .text_conversions import PokemonTextConversions
        data = [self.utils_class.end_of_line] * length
        min_length = min(length, len(string))
        for i in range(min_length):
            data[i] = PokemonTextConversions.convert_char_to_gen12_char(string[i]) & 0xFF
        return GSCTradingText(data, 0, length=length)

class GSCTradingMailData:
    """
    Class which contains mail data from the trading data.
    """

    mail_len = 0x41 # 0x21
    mail_len_old = 0x21
    sender_len = 0xE # INT: 0x8 for OT Name + 2 for message language + 2 for OT ID + 1 for Mon + 1 for Mail type
                     # KOR: 0xA for OT Name + 0 for message language + 2 for OT ID + 1 for Mon + 1 for Mail type
    language_sender_pos_int = 0x8
    reference_gen = 2

    def __init__(self, data_mail = None, data_sender = None):
        if data_mail is None:
            data_mail = [0]
        while len(data_mail) < self.mail_len:
            data_mail += [0]
        if data_sender is None:
            data_sender = [0]
        while len(data_sender) < self.sender_len:
            data_sender += [0]
        self.data_mail = GSCTradingText(data_mail, 0, length = self.mail_len)
        self.data_sender = GSCTradingText(data_sender, 0, length = self.sender_len)
        self.utils_class = self.get_utils_class()
    
    def get_utils_class(self):
        return GSCUtils

    def get_data_mail(self, is_new_mail_data = True):
        if is_new_mail_data:
            return self.data_mail.values
        return self.data_mail.values[:self.mail_len_old]

    def get_data_mail_sender(self):
        return self.data_sender.values

    def get_int_mail_data_language(mail_language_data, gen):
        from .text_conversions import PokemonNamesForGen
        language_str = PokemonNamesForGen.convert_generic_name_general_for_gen(mail_language_data, gen)
        if len(language_str) < 2:
            return PokemonNamesForGen.ENGLISH_LANGUAGE
        if language_str[0] != "E":
            return PokemonNamesForGen.ENGLISH_LANGUAGE
        if language_str[1] not in PokemonNamesForGen.language_str_short_list_small:
            return PokemonNamesForGen.ENGLISH_LANGUAGE
        return PokemonNamesForGen.sorted_languages_list[PokemonNamesForGen.language_str_short_list_small.index(language_str[1])]

    def get_mail_language(self):
        return GSCTradingMailData.get_int_mail_data_language(self.get_data_mail_sender()[self.language_sender_pos_int : self.language_sender_pos_int+2], self.reference_gen)

    def get_mail_language_data_for_language(language, gen):
        from .text_conversions import PokemonNamesForGen, PokemonTextConversions
        if (language == PokemonNamesForGen.ENGLISH_LANGUAGE) or (language not in PokemonNamesForGen.sorted_languages_list):
            return [0, 0]
        language_str = "E" + PokemonNamesForGen.language_str_short_list_small[PokemonNamesForGen.sorted_languages_list.index(new_language)]
        language_data = []
        for i in range(len(language_str)):
            language_data += [PokemonTextConversions.convert_char_to_genx_char(language_str[i], gen, None)]
        return language_data

    def set_mail_language(self, new_language):
        data_to_set = GSCTradingMailData.get_mail_language_data_for_language(new_language, self.reference_gen)
        for i in range(len(data_to_set)):
            self.data_sender.values[self.language_sender_pos_int + i] = data_to_set[i]

    def set_data_mail(self, data):
        max_copy_len = min(len(self.data_mail.values), len(data))
        for i in range(max_copy_len):
            self.data_mail.values[i] = data[i]
        if len(data) < len(self.data_mail.values):
            self.data_mail.values[len(data)] = self.utils_class.end_of_line

    def set_data_mail_sender(self, data):
        max_copy_len = min(len(self.data_sender.values), len(data))
        for i in range(max_copy_len):
            self.data_sender.values[i] = data[i]
    
class GSCTradingPartyInfo:
    """
    Class which contains information about the party size and species
    from the trading data.
    """
    max_party_mons = 6
    
    def __init__(self, data, start):
        # For debugging purposes
        if data is None:
            data = [0] * (self.max_party_mons + 1)
            start = 0
            data[0] = self.max_party_mons
        self.set_total(data[start])
        self.actual_mons = data[start + 1:start + 1 + self.max_party_mons]
    
    def get_id(self, pos):
        if pos >= self.get_total() or pos >= self.max_party_mons:
            return None
        return self.actual_mons[pos]
    
    def set_id(self, pos, val):
        if pos < self.get_total() and pos < self.max_party_mons:
            self.actual_mons[pos] = val
    
    def get_total(self):
        return self.total
    
    def set_total(self, value):
        self.total = value
        if self.total <= 0 or self.total > 6:
            self.total = 1

class GSCTradingPokémonInfo:
    """
    Class which contains information about the pokémon from the trading data.
    """
    unown_species = 201
    pokemon_data_len = 0x30
    ot_name_len = 0xB
    nickname_len = 0xB
    mail_len = 0x41 # 0x21
    mail_len_old = 0x21
    sender_len = 0xE # INT: 0x8 for OT Name + 2 for message language + 2 for OT ID + 1 for Mon + 1 for Mail type
                     # KOR: 0xA for OT Name + 0 for message language + 2 for OT ID + 1 for Mon + 1 for Mail type
    
    species_pos = 0
    item_pos = 1
    moves_pos = 2
    pps_pos = 0x17
    level_pos = 0x1F
    exp_pos = 8
    curr_hp_pos = 0x22
    stats_pos = 0x24
    evs_pos = 0xB
    ivs_pos = 0x15
    egg_cycles_pos = 0x1B
    status_pos = 0x20
    ot_id_pos = 6
    reference_gen = 2
    
    no_moves_equality_ranges = [range(0,2), range(6,0x17), range(0x1B, pokemon_data_len)]
    full_equality_ranges = [range(0, pokemon_data_len)]
    all_lengths = [pokemon_data_len, ot_name_len, nickname_len, mail_len, sender_len]
    all_lengths_old = [pokemon_data_len, ot_name_len, nickname_len, mail_len_old, sender_len]

    def __init__(self, data, start, length=pokemon_data_len):
        # For debugging purposes
        if data is None:
            data = [0] * length
            start = 0
        self.values = data[start:start+length]
        self.mail = None
        self._precalced_lengths = GSCUtilsMisc.calc_divide_lengths(self.all_lengths)
        self._precalced_lengths_old = GSCUtilsMisc.calc_divide_lengths(self.all_lengths_old)
        self.utils_class = self.get_utils_class()
        self.text_class = self.get_text_class()
    
    def get_utils_class(self):
        return GSCUtils
    
    def get_text_class(self):
        return GSCTradingText

    def add_ot_name(self, data, start):
        self.ot_name = self.text_class(data, start, length=self.ot_name_len)

    def set_ot_name(self, name):
        self.ot_name = self.text_class.create_from_string(name, length=self.ot_name_len)

    def get_ot_id(self):
        return GSCUtilsMisc.read_short(self.values, self.ot_id_pos)

    def set_ot_id(self, num):
        GSCUtilsMisc.write_short(self.values, self.ot_id_pos, num)

    def add_nickname(self, data, start):
        self.nickname = self.text_class(data, start, length=self.nickname_len)

    def add_mail(self, data, start, is_new_mail_data = True):
        if self.mail is None:
            self.mail = GSCTradingMailData()
        mail_len_data = self.mail_len_old
        if is_new_mail_data:
            mail_len_data = self.mail_len
        self.mail.set_data_mail(data[start:start+mail_len_data])
        
    def add_mail_sender(self, data, start):
        if self.mail is None:
            self.mail = GSCTradingMailData()
        self.mail.set_data_mail_sender(data[start:start+self.sender_len])
    
    def is_nicknamed(self, language):
        from .text_conversions import PokemonNamesForGen
        return not self.nickname.values_equal(PokemonNamesForGen.get_pokemon_name_for_gen(self.get_species(), self.reference_gen, language=language))

    def get_nickname_general(self, language):
        from .text_conversions import PokemonNamesForGen
        return PokemonNamesForGen.convert_generic_name_general_for_gen(self.nickname.values, self.reference_gen, language=language)

    def get_ot_name_general(self, language):
        from .text_conversions import PokemonNamesForGen
        return PokemonNamesForGen.convert_generic_name_general_for_gen(self.ot_name.values, self.reference_gen, language=language)
    
    def set_default_trainer_name(self, language):
        from .text_conversions import PokemonNamesForGen
        self.add_ot_name(PokemonNamesForGen.get_trainer_name_for_gen(self.reference_gen, language=language), 0)
    
    def set_default_nickname(self, language):
        from .text_conversions import PokemonNamesForGen
        self.add_nickname(PokemonNamesForGen.get_pokemon_name_for_gen(self.get_species(), self.reference_gen, language=language), 0)
    
    def set_egg_nickname(self, language):
        from .text_conversions import PokemonNamesForGen
        self.add_nickname(PokemonNamesForGen.get_egg_name_for_gen(self.reference_gen, language=language), 0)
    
    def get_species(self):
        return self.values[self.species_pos]
    
    def learnable_moves(self):
        """
        Returns the moves the pokémon could learn at its current level.
        """
        if self.get_species() in self.utils_class.learnsets.keys():
            if self.get_level() in self.utils_class.learnsets[self.get_species()].keys():
                return self.utils_class.learnsets[self.get_species()][self.get_level()]
        return None
    
    def set_species(self, data):
        self.values[self.species_pos] = data & 0xFF
        
    def get_item(self):
        return self.values[self.item_pos]
        
    def set_item(self, data=0):
        self.values[self.item_pos] = data & 0xFF
    
    def has_move_index(self, move, start=0):
        for i in range(start,4):
            if self.get_move(i) == move:
                return i
        return 4
    
    def has_move(self, move):
        if self.has_move_index(move) == 4:
            return False
        return True
    
    def free_move_slots(self):
        free_slots = []
        for i in range(4):
            if self.get_move(i) == GSCChecks.free_value_moves:
                free_slots += [i]
        return free_slots
    
    def get_move(self, pos):
        return self.values[self.moves_pos + pos]
    
    def set_move(self, pos, val, max_pp=True):
        self.values[self.moves_pos + pos] = val
        if max_pp:
            self.set_pp(pos, self.utils_class.moves_pp_list[val])

    # Default = trade-based friendship
    def set_friendship(self, val=None):
        if val is None:
            val = 70
        self.values[self.egg_cycles_pos] = val
    
    def set_hatching_cycles(self, val=1):
        self.values[self.egg_cycles_pos] = val
    
    def get_hatching_cycles(self):
        return self.values[self.egg_cycles_pos]
    
    def set_pp(self, pos, val):
        self.values[self.pps_pos + pos] = val
    
    def get_pp(self, pos):
        return self.values[self.pps_pos + pos]

    def get_max_pp(self, pos):
        pp_ups = (self.get_pp(pos) >> 6) & 3
        max_base_pp = self.utils_class.moves_pp_list[self.get_move(pos)]
        pp_increment = math.floor(max_base_pp/5)
        if max_base_pp == 40:
            pp_increment -= 1
        return max_base_pp + (pp_increment * pp_ups)

    def heal_move(self, pos):
        pp_ups = (self.get_pp(pos) >> 6) & 3
        self.set_pp(pos, (self.get_max_pp(pos)) | (pp_ups << 6))

    def heal_moves(self):
        for i in range(4):
            self.heal_move(i)
    
    def get_level(self):
        return self.values[self.level_pos]
    
    def set_level(self, val):
        self.values[self.level_pos] = val
        self.set_exp(self.utils_class.get_exp_level(self.get_species(), val, self.utils_class))
        self.update_stats()
    
    def set_exp(self, val):
        self.values[self.exp_pos] = (val >> 0x10) & 0xFF
        self.values[self.exp_pos+1] = (val >> 8) & 0xFF
        self.values[self.exp_pos+2] = (val) & 0xFF
    
    def update_stats(self):
        """
        Updates the stats after they're changed (from evolving/changing level).
        """
        old_max_hps = self.get_max_hp()
        old_current_hps = self.get_curr_hp()
        for i in range(self.utils_class.num_stats):
            GSCUtilsMisc.write_short(self.values, self.stats_pos + (i * 2), self.utils_class.stat_calculation(i, self.get_species(), self.get_ivs(), self.get_stat_exp(), self.get_level(), self.utils_class))
        new_max_hps = self.get_max_hp()
        old_current_hps += new_max_hps-old_max_hps
        GSCUtilsMisc.write_short(self.values, self.curr_hp_pos, min(max(0, old_current_hps), new_max_hps))
        
    def get_stat_exp(self):
        ret = [0,0,0,0,0]
        for i in range(5):
            ret[i] = GSCUtilsMisc.read_short(self.values, self.evs_pos + (i * 2))
        return ret

    def get_ivs(self):
        ret = [0,0,0,0]
        calc_val = [GSCUtilsMisc.read_nybbles(self.values[self.ivs_pos]), GSCUtilsMisc.read_nybbles(self.values[self.ivs_pos+1])]
        for i in range(4):
            ret[i] = calc_val[i>>1][i&1]
        return ret
    
    def get_unown_letter(self):
        ivs = self.get_ivs()
        letter_sum = 0
        for i in range(4):
            letter_sum |= ((ivs[i] >> 1) & 3) << (2 * (4 - 1 - i))
        return letter_sum // 10

    def get_curr_hp(self):
        return GSCUtilsMisc.read_short(self.values, self.curr_hp_pos)

    def heal(self):
        GSCUtilsMisc.write_short(self.values, self.curr_hp_pos, self.get_max_hp())
        self.values[self.status_pos] = 0

    def full_heal(self):
        self.heal()
        self.heal_moves()

    def faint(self):
        GSCUtilsMisc.write_short(self.values, self.curr_hp_pos, 0)
        self.values[self.status_pos] = 0
    
    def get_max_hp(self):
        return GSCUtilsMisc.read_short(self.values, self.stats_pos)
    
    def has_mail(self):
        return self.utils_class.is_item_mail(self.get_item())
    
    def is_equal(self, other, weak=False, all_values=False):
        ranges = self.no_moves_equality_ranges
        if all_values:
            ranges = self.full_equality_ranges
        for i in ranges:
            for j in i:
                if self.values[j] != other.values[j]:
                    return False
        if not self.are_moves_and_pp_same(other):
            return False
        if not weak:
            if not self.is_text_equal(other):
                return False
        return True

    def is_text_equal(self, other, do_mail = True):
        if not (self.ot_name.values_equal(other.ot_name.values) and self.nickname.values_equal(other.nickname.values)):
            return False
        if do_mail and self.has_mail():
            if not (self.mail.data_mail.values_equal(other.mail.data_mail.values) and self.mail.data_sender.values_equal(other.mail.data_sender.values)):
                return False
        return True

    # Process special characters we inject...
    # These can be done in synchronous mode as well...
    def apply_all_text_transforms_to_all(self, language):
        self.apply_all_text_transforms(self.ot_name, language)
        self.apply_all_text_transforms(self.nickname, language)
        if self.has_mail():
            self.apply_all_text_transforms(self.mail.data_mail, language, is_mail = True)
            self.apply_all_text_transforms(self.mail.data_sender, language, is_mail = True)

    def apply_all_text_transforms(self, text_entry, language, is_mail = False):
        self.apply_transform_kor_bad_chars(text_entry, language)
        self.apply_transform_protect_international_from_kor(text_entry, language, is_mail)
        self.apply_transform_protect_korean_from_jpn(text_entry, language, is_mail)

    def apply_transform_kor_bad_chars(self, text_entry, language):
        from .text_conversions import PokemonNamesForGen
        if language == PokemonNamesForGen.KOREAN_LANGUAGE:
            return

        for i in range(len(text_entry.values)):
            if text_entry.values[i] == self.utils_class.end_of_line:
                break
            if text_entry.values[i] in self.utils_class.bad_ids_text_special_from_kor.keys():
                text_entry.values[i] = self.utils_class.bad_ids_text_special_from_kor[text_entry.values[i]]

    def apply_transform_protect_international_from_kor(self, text_entry, language, is_mail):
        from .text_conversions import PokemonNamesForGen
        if language != PokemonNamesForGen.KOREAN_LANGUAGE:
            return
        if is_mail:
            return
        if text_entry.values[0] != self.utils_class.korean_special_replacement:
            # Pre-applied
            return

        in_chars = []
        out_chars = []
        container_obj = types.SimpleNamespace()
        container_obj.has_encountered_eol = False
        for i in range(1, len(text_entry.values)):
            in_val = text_entry.values[i]
            if in_val == self.utils_class.prohibited_char_replacement:
                in_val = self.utils_class.prohibited_char
            in_chars += [in_val]
            out = self.utils_class.apply_text_transform_protect_international_from_korean_special(self.utils_class, in_chars, container_obj)
            out_chars += out
            if self.utils_class.end_of_line in out:
                container_obj.has_encountered_eol = True

        for i in range(len(text_entry.values)):
            text_entry.values[i] = out_chars[i]

    def apply_transform_protect_korean_from_jpn(self, text_entry, language, is_mail):
        from .text_conversions import PokemonNamesForGen
        if language == PokemonNamesForGen.KOREAN_LANGUAGE:
            return
        if is_mail:
            return
        if text_entry.values[0] != self.utils_class.korean_patched_special_replacement:
            return

        in_chars = []
        out_chars = []
        for i in range(1, len(text_entry.values)):
            in_val = text_entry.values[i]
            if in_val == self.utils_class.prohibited_char_replacement:
                in_val = self.utils_class.prohibited_char
            in_chars += [in_val]
            out_chars += self.utils_class.apply_text_transform_protect_korean_from_jpn_special(self.utils_class, in_chars)

        for i in range(len(text_entry.values)):
            text_entry.values[i] = out_chars[i]

    # Inject special characters and patch out bad chars for specific languages.
    # This can only be done with all the data available, so buffered only.
    # But the unpatching can be done in synchronous mode as well by the checks.
    def patch_out_bad_chars_for_language_buffered_only(self, target_language, checks, is_egg):
        from .text_conversions import PokemonNamesForGen
        if target_language is None:
            return

        own_data = self.utils_class.single_mon_to_data(self, is_egg)
        ret_data = self.utils_class.single_mon_from_data_multilanguage(checks, own_data)
        # HOW?!
        if ret_data is None:
            return
        # Get the languages for which this mon's data is valid...
        language_value = ret_data[2]
        is_korean_2bytes_valid = (language_value & (1 << GSCUtils.korean_language_2_bytes_special_language)) != 0
        valid_languages_list = self.utils_class.convert_language_int_to_list(language_value)

        if (target_language == PokemonNamesForGen.KOREAN_LANGUAGE) and (valid_languages_list == [PokemonNamesForGen.JAPANESE_LANGUAGE]): # This automatically means it's not 2-bytes Korean
            self.utils_class.patch_out_bad_chars_protect_korean_from_jpn_buffered_only(self.utils_class, self.ot_name)
            self.utils_class.patch_out_bad_chars_protect_korean_from_jpn_buffered_only(self.utils_class, self.nickname)

        if (target_language != PokemonNamesForGen.KOREAN_LANGUAGE) and (valid_languages_list == [PokemonNamesForGen.KOREAN_LANGUAGE]) and is_korean_2bytes_valid:
            self.utils_class.patch_out_bad_chars_protect_international_from_korean_buffered_only(self.utils_class, self.ot_name)
            self.utils_class.patch_out_bad_chars_protect_international_from_korean_buffered_only(self.utils_class, self.nickname)

    def get_same_moves(self):
        """
        Returns for each index the list of indexes with the same move.
        """
        pos = []
        for i in range(4):
            inner_pos = []
            for j in range(4):
                if self.get_move(i) == self.get_move(j):
                    inner_pos += [i]
            pos += [inner_pos]
        return pos
        
    def are_moves_and_pp_same(self, other):
        corresponding_indexes = self.are_moves_same(other)
        if corresponding_indexes is None:
            return False
        possible_positions = self.get_same_moves()
        found_pos = []
        for i in range(4):
            found = False
            for j in possible_positions[i]:
                if not found and corresponding_indexes[j] not in found_pos and self.get_pp(i) == other.get_pp(corresponding_indexes[j]):
                    found_pos += [corresponding_indexes[j]]
                    found = True
            if not found:
                return False
        return True
    
    def are_moves_same(self, other):
        """
        Returns None if the moves are different.
        If they're the same, it returns the index in which they're found.
        """
        pos = []
        for i in range(4):
            proper_found = False
            start_index = 0
            while not proper_found:
                index = other.has_move_index(self.get_move(i), start=start_index)
                if index == 4:
                    return None
                elif index in pos:
                    start_index = index + 1
                else:
                    pos += [index]
                    proper_found = True
        return pos
    
    def has_changed_significantly(self, raw):
        """
        Returns whether a pokémon has changed too much due to the sanity
        checks cleaning it.
        """
        if self.get_species() != raw.get_species():
            return True
        if self.are_moves_same(raw) is None:
            return True
        if self.get_level() != raw.get_level():
            return True
        return False

    def get_data(self, is_new_mail_data = True):
        """
        Returns all the data used to represent this pokemon.
        """
        sources = [self.values, self.ot_name.values, self.nickname.values]
        relevant_lengths = self._precalced_lengths
        if not is_new_mail_data:
            relevant_lengths = self._precalced_lengths_old
        if self.has_mail():
            mail_sources = [self.mail.get_data_mail(is_new_mail_data = is_new_mail_data), self.mail.get_data_mail_sender()]
        else:
            mail_sources = [None, None]
        data = [0] * relevant_lengths[len(sources)+len(mail_sources)]
        for i in range(len(sources)):
            GSCUtilsMisc.copy_to_data(data, relevant_lengths[i], sources[i])
        if self.has_mail():
            for i in range(len(mail_sources)):
                GSCUtilsMisc.copy_to_data(data, relevant_lengths[i+len(sources)], mail_sources[i])
        return data

    def set_data(data, is_new_mail_data = True):
        """
        Creates an entry from the given data.
        """
        mon = GSCTradingPokémonInfo(data, 0)
        relevant_lengths = mon._precalced_lengths
        if not is_new_mail_data:
            relevant_lengths = mon._precalced_lengths_old
        mon.add_ot_name(data,relevant_lengths[1])
        mon.add_nickname(data, relevant_lengths[2])
        if mon.has_mail():
            mon.add_mail(data, relevant_lengths[3], is_new_mail_data = is_new_mail_data)
            mon.add_mail_sender(data, relevant_lengths[4])
        return mon

    def create_from_scratch(species = 1, item = 0, level = 2, moves = [1, 2, 3, 4], ot_name = "AAAAA", ot_id = 1, language = 0):
        """
        Creates an entry from no data.
        """
        mon = GSCTradingPokémonInfo(None, 0)
        mon.set_species(species)
        mon.set_item(item)
        mon.set_level(level)
        for i in range(len(moves)):
            mon.set_move(i, moves[i])
        mon.set_default_nickname(language)
        mon.set_ot_name(ot_name)
        mon.set_ot_id(ot_id)
        mon.heal()
        return mon

class GSCTradingData:
    """
    Class which contains all the informations about a trader's party.
    """
    trader_name_pos = 0
    trading_party_info_pos = 0xB
    trading_party_final_pos = 0x12
    trader_info_pos = 0x13
    trading_pokemon_pos = 0x15
    trading_pokemon_ot_pos = 0x135
    trading_pokemon_nickname_pos = 0x177
    
    trading_pokemon_length = 0x30
    trading_name_length = 0xB
    trading_mail_length = 0x41 # 0x21
    trading_mail_length_old = 0x21
    trading_mail_sender_length = 0xE

    trading_pokemon_mail_pos = 0
    trading_pokemon_mail_sender_pos = trading_mail_length * 6
    trading_pokemon_mail_sender_old_pos = trading_mail_length_old * 6
    
    def __init__(self, data_pokemon, data_mail=None, do_full=True, is_new_mail_data = True):
        self.utils_class = self.get_utils_class()

        # For debugging purposes
        if data_pokemon is None:
            self.trader = self.get_text_class().create_from_string("Server", length=self.trading_name_length)
            self.party_info = self.party_generator(None, 0)
            self.trader_info = 1
            self.pokemon = []
            if do_full:
                for i in range(self.get_party_size()):
                    self.pokemon += [self.mon_generator_class().create_from_scratch()]
                    self.party_info.set_id(i, self.pokemon[i].get_species())
            return

        # Regular code
        self.trader = self.text_generator(data_pokemon, self.trader_name_pos, length=self.trading_name_length)
        self.party_info = self.party_generator(data_pokemon, self.trading_party_info_pos)
        self.trader_info = self.trainer_info_generator(data_pokemon, self.trader_info_pos)
        self.pokemon = []
        if do_full:
            for i in range(self.get_party_size()):
                self.pokemon += [self.mon_generator(data_pokemon, self.trading_pokemon_pos + i * self.trading_pokemon_length)]
                self.pokemon[i].add_ot_name(data_pokemon, self.trading_pokemon_ot_pos + i * self.trading_name_length)
                self.pokemon[i].add_nickname(data_pokemon, self.trading_pokemon_nickname_pos + i * self.trading_name_length)
                if (data_mail is not None) and self.pokemon[i].has_mail():
                    if is_new_mail_data:
                        self.pokemon[i].add_mail(data_mail, self.trading_pokemon_mail_pos + i * self.trading_mail_length, is_new_mail_data = is_new_mail_data)
                        self.pokemon[i].add_mail_sender(data_mail, self.trading_pokemon_mail_sender_pos + i * self.trading_mail_sender_length)
                    else:
                        self.pokemon[i].add_mail(data_mail, self.trading_pokemon_mail_pos + i * self.trading_mail_length_old, is_new_mail_data = is_new_mail_data)
                        self.pokemon[i].add_mail_sender(data_mail, self.trading_pokemon_mail_sender_old_pos + i * self.trading_mail_sender_length)
    
    def mon_generator(self, data, pos):
        return self.mon_generator_class()(data, pos)
    
    def mon_generator_class(self):
        return GSCTradingPokémonInfo
    
    def text_generator(self, data, pos, length=trading_name_length):
        return GSCTradingText(data, pos, length=length)
    
    def party_generator(self, data, pos):
        return GSCTradingPartyInfo(data, pos)
    
    def trainer_info_generator(self, data, pos):
        return GSCUtilsMisc.read_short(data, pos)
    
    def get_utils_class(self):
        return GSCUtils
    
    def get_text_class(self):
        return GSCTradingText

    def check_pos_validity(func):
        def wrapper(*args, **kwargs):
            self = args[0]
            pos = args[1]
            if pos < 0 or pos >= self.get_party_size():
                print(GSCTradingStrings.index_error_str)
                return False
            return func(*args, **kwargs)
        return wrapper
    
    def get_party_size(self):
        return self.party_info.get_total()
    
    def get_last_mon_index(self):
        return self.get_party_size()-1
    
    def search_for_mon(self, mon, is_egg):
        """
        Returns None if a provided pokémon is not in the party.
        Otherwise, it returns their index.
        """
        for i in range(self.get_party_size()):
            if mon.is_equal(self.pokemon[i]) and (self.is_mon_egg(i) == is_egg):
                return i
        for i in range(self.get_party_size()):
            if mon.is_equal(self.pokemon[i], weak=True) and (self.is_mon_egg(i) == is_egg):
                return i
        return None

    @check_pos_validity
    def mon_has_mail(self, pos):
        return self.pokemon[pos].has_mail()

    @check_pos_validity
    def is_mon_egg(self, pos):
        return self.party_info.get_id(pos) == self.utils_class.egg_id

    def party_has_mail(self):
        mail_owned = False
        for i in range(self.get_party_size()):
            mail_owned |= self.mon_has_mail(i)
        return mail_owned
    
    def evolution_procedure(self, pos, evolution, language):
        """
        Procedure which actually evolves the Pokémon in the data.
        """
        reset_name = False
        if not self.pokemon[pos].is_nicknamed(language):
            reset_name = True
        self.pokemon[pos].set_species(evolution)
        if reset_name:
            self.pokemon[pos].set_default_nickname(language)
        self.party_info.set_id(pos, self.pokemon[pos].get_species())
        self.pokemon[pos].update_stats()

    @check_pos_validity
    def requires_input(self, pos, special_mons_set):
        """
        Handles detemining if the mon requires special care
        """
        result = GSCUtilsMisc.default_if_none(self.evolve_mon(pos), False)
        if not result:
            result = self.is_special_mon(pos, special_mons_set)
        return result

    @check_pos_validity
    def evolve_mon(self, pos):
        """
        Handles evolving a pokémon in the party.
        Returns None if it won't evolve.
        Returns True if it evolved and player input is required.
        Returns False if it evolved and no player input is required.
        """
        evolution = self.utils_class.get_evolution(self.pokemon[pos].get_species(), self.pokemon[pos].get_item())
        if evolution is None or self.is_mon_egg(pos):
            return None
        evo_item = self.utils_class.get_evolution_item(self.pokemon[pos].get_species())
        if evo_item is not None:
            self.pokemon[pos].set_item()
        self.evolution_procedure(pos, evolution)
        curr_learning = self.pokemon[pos].learnable_moves()
        if curr_learning is not None:
            for i in range(len(curr_learning)):
                if not self.pokemon[pos].has_move(curr_learning[i]):
                    free_slots = self.pokemon[pos].free_move_slots()
                    if len(free_slots) > 0:
                        self.pokemon[pos].set_move(free_slots[0], curr_learning[i])
                    else:
                        return True
        return False
        
    @check_pos_validity
    def is_special_mon(self, pos, special_mons_set):
        """
        Handles special pokémon which may learn new moves.
        Returns True if it is a special mon.
        Returns False if not.
        """
        return self.pokemon[pos].get_species() in special_mons_set

    def heal_party(self):
        """
        Fully heals the entire party.
        """
        len_party = self.get_party_size()
        if len(self.pokemon) < len_party:
            len_party = len(self.pokemon)
        for i in range(len_party):
            self.pokemon[i].full_heal()

    def get_traded_mons(self, other):
        """
        Gets which pokémon were traded.
        """
        return [self.pokemon[self.get_last_mon_index()].get_species(), other.pokemon[other.get_last_mon_index()].get_species()]

    def patch_out_bad_chars_for_language_buffered_only_player(self, other_language, target_language, checks):
        from .text_conversions import PokemonNamesForGen
        if target_language is None:
            return
        if other_language is None:
            return

        if (target_language == PokemonNamesForGen.KOREAN_LANGUAGE) and (other_language == PokemonNamesForGen.JAPANESE_LANGUAGE):
            self.utils_class.patch_out_bad_chars_protect_korean_from_jpn_buffered_only(self.utils_class, self.trader)

        if (target_language != PokemonNamesForGen.KOREAN_LANGUAGE) and (other_language == PokemonNamesForGen.KOREAN_LANGUAGE):
            self.utils_class.patch_out_bad_chars_protect_international_from_korean_buffered_only(self.utils_class, self.trader)

    def patch_out_bad_chars_for_language_buffered_only(self, other_language, target_language):
        checks = self.utils_class.get_basic_checks()
        self.patch_out_bad_chars_for_language_buffered_only_player(other_language, target_language, checks)
        for i in range(self.get_party_size()):
            self.pokemon[i].patch_out_bad_chars_for_language_buffered_only(target_language, checks, self.is_mon_egg(i))
    
    def trade_mon(self, other, own_index, other_index, checks):
        """
        Trades a pokémon between two parties.
        """
        # Prepare checks
        checks.reset_species_item_list()
        checks.set_single_team_size()
        checks.reset_text_buffers()
        checks.prepare_patch_sets_buffer()
        checks.prepare_species_buffer()

        # Account for mail shenanigans
        if self.mon_has_mail(own_index):
            from .text_conversions import PokemonNamesForGen
            # Avoid patching a new newline and end of line in a converted korean mail...
            if self.pokemon[own_index].mail.get_mail_language() == PokemonNamesForGen.KOREAN_LANGUAGE:
                checks.do_mail_newline_checks = False
        
        # Apply checks
        own_id = checks.species_cleaner(self.party_info.get_id(own_index))
        checks.prepare_species_buffer()
        own = self.mon_generator_class().set_data(checks.apply_checks_to_data(checks.single_pokemon_checks_map, self.pokemon[own_index].get_data()))
        
        # Actually trade the Pokémon
        self.reorder_party(own_index)
        other.reorder_party(other_index)
        self.pokemon[self.get_last_mon_index()] = other.pokemon[other.get_last_mon_index()]
        other.pokemon[other.get_last_mon_index()] = own
        checks.curr_species_pos = self.get_last_mon_index()
        checks.team_size = self.get_party_size()
        self.party_info.set_id(self.get_last_mon_index(), other.party_info.get_id(other.get_last_mon_index()))
        other.party_info.set_id(other.get_last_mon_index(), own_id)
        if not self.is_mon_egg(self.get_last_mon_index()):
            self.pokemon[self.get_last_mon_index()].set_friendship()
        if not other.is_mon_egg(other.get_last_mon_index()):
            other.pokemon[other.get_last_mon_index()].set_friendship()
    
    @check_pos_validity
    def reorder_party(self, traded_pos):
        """
        Moves a pokémon at the end of the party.
        """
        pa_info = self.party_info.get_id(traded_pos)
        po_data = self.pokemon[traded_pos]
        for i in range(traded_pos+1,self.get_party_size()):
            self.party_info.set_id(i-1, self.party_info.get_id(i))
            self.pokemon[i-1] = self.pokemon[i]
        self.party_info.set_id(self.get_last_mon_index(), pa_info)
        self.pokemon[self.get_last_mon_index()] = po_data

    def create_trading_data(self, lengths, is_new_mail_data = True):
        """
        Creates the data which can be loaded to the hardware.
        """
        data = []
        for i in range(3):
            data += [lengths[i]*[0]]
        if is_new_mail_data:
            data += [self.utils_class.no_mail_section[:len(self.utils_class.no_mail_section)]]
        else:
            data += [self.utils_class.no_mail_section_old[:len(self.utils_class.no_mail_section_old)]]
        GSCUtilsMisc.copy_to_data(data[1], self.trader_name_pos, self.trader.values, self.trading_name_length)
        data[1][self.trading_party_info_pos] = self.get_party_size()
        GSCUtilsMisc.copy_to_data(data[1], self.trading_party_info_pos + 1, self.party_info.actual_mons)
        data[1][self.trading_party_final_pos] = 0xFF
        if self.trader_info is not None:
            GSCUtilsMisc.write_short(data[1], self.trader_info_pos, self.trader_info)
        for i in range(self.get_party_size()):
            GSCUtilsMisc.copy_to_data(data[1], self.trading_pokemon_pos + (i * self.trading_pokemon_length), self.pokemon[i].values)
            GSCUtilsMisc.copy_to_data(data[1], self.trading_pokemon_ot_pos + (i * self.trading_name_length), self.pokemon[i].ot_name.values, self.trading_name_length)
            GSCUtilsMisc.copy_to_data(data[1], self.trading_pokemon_nickname_pos + (i * self.trading_name_length), self.pokemon[i].nickname.values, self.trading_name_length)
            if self.pokemon[i].mail is not None:
                real_tml = self.trading_mail_length_old
                real_tpmsp = self.trading_pokemon_mail_sender_old_pos
                if is_new_mail_data:
                    real_tml = self.trading_mail_length
                    real_tpmsp = self.trading_pokemon_mail_sender_pos
                GSCUtilsMisc.copy_to_data(data[3], self.trading_pokemon_mail_pos + (i * real_tml), self.pokemon[i].mail.get_data_mail(is_new_mail_data = is_new_mail_data))
                GSCUtilsMisc.copy_to_data(data[3], real_tpmsp + (i * self.trading_mail_sender_length), self.pokemon[i].mail.get_data_mail_sender(), self.trading_mail_sender_length)
        self.utils_class.create_patches_data(data[1], data[2], self.utils_class)
        self.utils_class.create_patches_data(data[3], data[3], self.utils_class, is_mail=True, is_old_mail_data = not is_new_mail_data)
        return data
    
class GSCChecks:
    """
    Class which handles sanity checks and cleaning of the received data.
    checks_map and single_pokemon_checks_map are its product used to apply
    the checks.
    """
    base_folder = "useful_data/gsc/"
    bad_ids_items_path = "bad_ids_items.bin"
    bad_ids_moves_path = "bad_ids_moves.bin"
    bad_ids_pokemon_path = "bad_ids_pokemon.bin"
    bad_ids_text_path = "bad_ids_text.bin"
    checks_map_path = "checks_map.bin"
    checks_map_old_path = "checks_map_old.bin"
    single_pokemon_checks_map_path = "single_pokemon_checks_map.bin"
    single_pokemon_checks_map_old_path = "single_pokemon_checks_map_old.bin"
    moves_checks_map_path = "moves_checks_map.bin"
    pokemon_patch_set_0_path = "pokemon_patch_set_0.bin"
    pokemon_patch_set_1_path = "pokemon_patch_set_1.bin"
    mail_patch_set_path = "mail_patch_set.bin"
    mail_patch_set_old_path = "mail_patch_set_old.bin"
    japanese_mail_patch_set_path = "japanese_mail_patch_set.bin"
    
    curr_exp_pos_masks = [0, 0xFF0000, 0xFFFF00]
    free_value_species = 0xFF
    empty_value_species = 0
    free_value_moves = 0
    no_conversion_patch = 0
    end_of_patch = 0xFF
    patch_set_cover = 0xFC
    trainer_name_id = 0x5D # Needed by Korean, which doesn't support this character
    tackle_id = 0x21
    rattata_id = 0x13
    question_mark = 0xE6
    question_mark_kor = [0x0B, 0x67]
    newline = 0x4E
    newline_kor = 0x59
    mail_replaced_fe = 0x21
    mail_replaced_fe_kor = 0x51
    max_mail_line_length = 16
    reference_gen = 2
    mail_text_null = 0
    
    def __init__(self, section_sizes, do_sanity_checks, language = None, set_default_nickname = False, set_default_ot = False, set_default_partner = False, do_profanity_checks = False, use_strict_language_checks = False, section_sizes_old = None, use_strict_language_checks_mail = False):
        if language is None:
            from .text_conversions import PokemonNamesForGen
            language = PokemonNamesForGen.ENGLISH_LANGUAGE
        self.language = language
        self.set_default_nickname = set_default_nickname
        self.set_default_ot = set_default_ot
        self.set_default_partner = set_default_partner
        self.do_profanity_checks = do_profanity_checks
        self.use_strict_language_checks = use_strict_language_checks
        self.use_strict_language_checks_mail = use_strict_language_checks_mail
        self.do_mail_newline_checks = True

        self.utils_class = self.get_utils_class()
        self.do_sanity_checks = do_sanity_checks
        self.bad_ids_items = GSCUtilsLoaders.prepare_check_list(GSCUtilsMisc.read_data(self.get_path(self.bad_ids_items_path)))
        self.bad_ids_moves = GSCUtilsLoaders.prepare_check_list(GSCUtilsMisc.read_data(self.get_path(self.bad_ids_moves_path)))
        self.bad_ids_pokemon = GSCUtilsLoaders.prepare_check_list(GSCUtilsMisc.read_data(self.get_path(self.bad_ids_pokemon_path)))
        self.bad_ids_text = GSCUtilsLoaders.prepare_check_list(GSCUtilsMisc.read_data(self.get_path(self.bad_ids_text_path)))
        self.pokemon_patch_sets = [GSCUtilsLoaders.prepare_check_list(GSCUtilsMisc.read_data(self.get_path(self.pokemon_patch_set_0_path))), GSCUtilsLoaders.prepare_check_list(GSCUtilsMisc.read_data(self.get_path(self.pokemon_patch_set_1_path)))]
        self.mail_patch_set = [GSCUtilsLoaders.prepare_check_list(GSCUtilsMisc.read_data(self.get_path(self.mail_patch_set_path)))]
        self.mail_patch_set_old = [GSCUtilsLoaders.prepare_check_list(GSCUtilsMisc.read_data(self.get_path(self.mail_patch_set_old_path)))]
        self.japanese_mail_patch_set = [GSCUtilsLoaders.prepare_check_list(GSCUtilsMisc.read_data(self.get_path(self.mail_patch_set_path)))]
        self.check_functions = [
            self.clean_nothing,
            self.clean_text,
            self.clean_team_size,
            self.clean_species,
            self.clean_move,
            self.clean_item,
            self.clean_level,
            self.check_hp,
            self.clean_text_final,
            self.load_stat_exp,
            self.load_stat_iv,
            self.check_stat,
            self.clean_species_sp,
            self.clean_pp,
            self.clean_experience,
            self.clean_egg_cycles_friendship,
            self.clean_type,
            self.clean_text_newline,
            self.clean_text_final_no_end,
            self.clean_species_force_terminate,
            self.clean_mail_species,
            self.clean_mail_item,
            self.clean_mail_same_species,
            self.clean_pokemon_patch_set,
            self.clean_mail_patch_set,
            self.clean_japanese_mail_patch_set,
            self.clean_text_partner,
            self.clean_text_partner_maybe_final,
            self.clean_text_nickname,
            self.clean_text_nickname_final,
            self.clean_text_ot,
            self.clean_text_ot_maybe_final,
            self.clean_text_partner_final,
            self.clean_text_ot_final,
            self.clean_text_ot_maybe_final_no_end,
            self.clean_text_mail,
            self.clean_text_mail_check_newline_int,
            self.clean_text_mail_check_newline_kor_final_int,
            self.clean_text_mail_final,
            self.clean_text_nickname_special_char_check,
            self.clean_text_ot_special_char_check,
            self.clean_text_partner_special_char_check,
            self.clean_text_ot_final_no_end,
            self.clean_text_ot_mail_start,
            ]
        self.checks_map = self.prepare_checks_map(GSCUtilsMisc.read_data(self.get_path(self.checks_map_path)), section_sizes, self.check_functions)
        if section_sizes_old is None:
            section_sizes_old = section_sizes
        self.checks_map_old = self.prepare_checks_map(GSCUtilsMisc.read_data(self.get_path(self.checks_map_old_path)), section_sizes_old, self.check_functions)
        self.single_pokemon_checks_map = GSCUtilsLoaders.prepare_functions_map(GSCUtilsMisc.read_data(self.get_path(self.single_pokemon_checks_map_path)), self.check_functions)
        self.single_pokemon_checks_map_old = GSCUtilsLoaders.prepare_functions_map(GSCUtilsMisc.read_data(self.get_path(self.single_pokemon_checks_map_old_path)), self.check_functions)
        self.moves_checks_map = GSCUtilsLoaders.prepare_functions_map(GSCUtilsMisc.read_data(self.get_path(self.moves_checks_map_path)), self.check_functions)
        self.species_cleaner = self.clean_species_sp
    
    def get_path(self, target):
        return self.base_folder + target
    
    def get_utils_class(self):
        return GSCUtils
    
    def clean_check_sanity_checks(func):
        def wrapper(*args, **kwargs):
            self = args[0]
            val = args[1]
            if self.do_sanity_checks:
                val = func(*args, **kwargs)
            return val
        return wrapper
    
    def valid_check_sanity_checks(func):
        def wrapper(*args, **kwargs):
            self = args[0]
            if self.do_sanity_checks:
                return func(*args, **kwargs)
            else:
                return True
        return wrapper
    
    def apply_checks_to_data(self, checker, data):
        new_data = []
        for j in range(len(checker)):
            checked_value = checker[j](data[j])
            if not isinstance(checked_value, list):
                checked_value = [checked_value]
            new_data += checked_value
        return new_data

    def prepare_text_buffer(self):
        self.curr_text = []
        self.last_text_converted = ""
        self.is_bad_text_redeemable = False
        self.last_considered_char = None
        self.is_curr_text_two_bytes = None
        self.last_two_bytes_error = False
        self.force_default_name = False
        self.force_next_eol = False
        self.is_mail = False
        self.is_mail_ot = False
        self.do_special_chars_check = False
        self.is_korean_special = False
        self.is_patched_for_korean_special = False
        self.special_chars_list = []
        self.is_korean_special_was_japanese_truncated = False
        
    def reset_species_item_list(self):
        self.species_list = []
        self.species_list_size = 0
        self.item_list = []

    def reset_text_buffers(self):
        self.prepare_text_buffer()
        self.has_encountered_eol = False
        self.has_encountered_newline = False
        self.curr_species_nickname = 0
        self.last_species_nickname = -1
        self.curr_species_ot = 0
        self.last_species_ot = -1
        self.do_mail_newline_checks = True

    def set_single_team_size(self):
        self.team_size = 1
        
    def add_to_species_list(self, species):
        if (species != self.free_value_species) and (species != self.empty_value_species):
            self.species_list_size += 1
        self.species_list += [species]
        
    def prepare_species_buffer(self):
        self.curr_species_pos = 0
        
    def prepare_patch_sets_buffer(self):
        self.curr_patch_set = 0

    def prepare_checks_map(self, data, lengths, functions_list):
        raw_data_sections = GSCUtilsMisc.divide_data(data, lengths)
        call_map = [[],[],[],[]]
        for i in range(len(raw_data_sections)):
            call_map[i] = GSCUtilsLoaders.prepare_functions_map(raw_data_sections[i], functions_list)
        return call_map
    
    @clean_check_sanity_checks
    def clean_nothing(self, val):
        return val
    
    @clean_check_sanity_checks
    def clean_level(self, level):
        self.level = self.utils_class.get_level_exp(self.curr_species, self.exp, self.utils_class)
        return self.level
    
    def exp_range_calculations(self):
        return [self.utils_class.get_exp_level(self.curr_species, self.utils_class.min_level, self.utils_class), self.utils_class.get_exp_level(self.curr_species, self.utils_class.max_level, self.utils_class)]
    
    @clean_check_sanity_checks
    def clean_experience(self, val):
        if self.curr_exp_pos == 0:
            self.exp_range = self.exp_range_calculations()
            if val >= 0x80:
                self.negative_exp = True
        if self.negative_exp:
            val = 0
        curr_read_val = val << (8 * (2 - self.curr_exp_pos))
        exp_mask = self.curr_exp_pos_masks[self.curr_exp_pos]
        self.exp = self.check_range(self.exp_range, (self.exp & exp_mask) | curr_read_val)
        val = (self.exp >> (8 * (2 - self.curr_exp_pos))) & 0xFF
        self.curr_exp_pos += 1
        return val

    def clean_team_size(self, team_size):
        self.team_size = self.clean_value(team_size, self.is_team_size_valid, 1)
        return self.team_size
    
    @clean_check_sanity_checks
    def clean_item(self, item):
        cleaned_item = self.clean_value(item, self.is_item_valid, 0)
        self.item_list += [cleaned_item]
        return cleaned_item
    
    @clean_check_sanity_checks
    def clean_pp(self, pp):
        current_pp = pp & 0x3F
        pp_ups = (pp >> 6) & 3
        max_base_pp = self.utils_class.moves_pp_list[self.moves[self.curr_pp]]
        pp_increment = math.floor(max_base_pp/5)
        if max_base_pp == 40:
            pp_increment -= 1
        max_pp = max_base_pp + (pp_increment * pp_ups)
        final_pp = pp
        if current_pp > max_pp:
            final_pp = (pp_ups << 6) | max_pp
        self.curr_pp += 1
        return final_pp
    
    @clean_check_sanity_checks
    def clean_move(self, move):
        if move == GSCChecks.free_value_moves and self.curr_move > 0:
            self.moves[self.curr_move] = GSCChecks.free_value_moves
            self.curr_move += 1
            return move
        final_move = self.clean_value(move, self.is_move_valid, self.tackle_id)
        self.moves[self.curr_move] = final_move
        self.curr_move += 1
        return final_move
    
    @clean_check_sanity_checks
    def clean_species(self, species):
        self.curr_species = self.clean_value(species, self.is_species_valid, self.rattata_id)
        self.curr_species_pos += 1
        self.curr_stat_id = 0
        self.iv = [0,0,0,0]
        self.stat_exp = [0,0,0,0,0]
        self.moves = [0,0,0,0]
        self.curr_move = 0
        self.curr_pp = 0
        self.exp = 0
        self.negative_exp = False
        self.curr_exp_pos = 0
        self.curr_hp = 0
        self.curr_pos = 0
        self.curr_iv_pos = 0
        self.curr_exp_id = 0
        self.curr_stat_exp_pos = 0
        return self.curr_species

    def get_species_is_egg(self, species):
        return species == self.utils_class.egg_id

    def clean_species_sp(self, species):
        if species == self.free_value_species or self.species_list_size >= self.team_size:
            self.add_to_species_list(self.free_value_species)
            self.curr_species_pos += 1
            if self.do_sanity_checks:
                return self.free_value_species
            return species
        found_species = self.clean_value(species, self.is_species_valid, self.rattata_id)
        if self.get_species_is_egg(species):
            found_species = species
        self.add_to_species_list(found_species)
        self.curr_species_pos += 1
        if self.do_sanity_checks:
            return found_species
        return species

    def clean_species_force_terminate(self, species):
        self.prepare_species_buffer()
        if self.do_sanity_checks:
            return self.free_value_species
        return species
    
    @clean_check_sanity_checks
    def load_stat_exp(self, val):
        calc_val = val << (8 * (1 - (self.curr_stat_exp_pos & 1)))
        if self.curr_stat_exp_pos == 0:
            self.stat_exp[self.curr_exp_id] = calc_val
            self.curr_stat_exp_pos += 1
        else:
            self.stat_exp[self.curr_exp_id] |= calc_val
            self.curr_stat_exp_pos = 0
            self.curr_exp_id += 1
        return val
    
    @clean_check_sanity_checks
    def load_stat_iv(self, val):
        calc_val = GSCUtilsMisc.read_nybbles(val)
        self.iv[self.curr_iv_pos*2] = calc_val[0]
        self.iv[(self.curr_iv_pos*2) + 1] = calc_val[1]
        self.curr_iv_pos += 1
        return val
    
    @clean_check_sanity_checks
    def clean_mail_species(self, species):
        self.curr_species_pos += 1
        return self.species_list[self.curr_species_pos-1]
    
    @clean_check_sanity_checks
    def clean_mail_same_species(self, species):
        return self.species_list[self.curr_species_pos-1]
    
    @clean_check_sanity_checks
    def clean_mail_item(self, item):
        return self.item_list[self.curr_species_pos-1]

    @clean_check_sanity_checks
    def clean_char_eol(self, char):
        # Allow whatever as long as it is after EOL
        char_val = char
        if not self.has_encountered_eol:
            char_val = self.utils_class.end_of_line
            self.has_encountered_eol = True
        return char_val

    def clean_text(self, char):
        from .text_conversions import PokemonNamesForGen
        # Do runtime conversions for improved compatibility between versions
        if self.do_special_chars_check:
            # Only do them if needed...
            if (char == self.utils_class.korean_special_replacement) and (self.language == PokemonNamesForGen.KOREAN_LANGUAGE):
                self.is_korean_special = True
                return []
            if (char == self.utils_class.korean_patched_special_replacement) and (self.language != PokemonNamesForGen.KOREAN_LANGUAGE):
                self.is_patched_for_korean_special = True
                return []
        char_val = self.clean_text_value(char, self.is_char_valid)
        self.curr_text += [char_val]
        if self.last_considered_char is None:
            self.last_text_converted = PokemonNamesForGen.convert_generic_name_general_for_gen(self.curr_text, self.reference_gen, language=self.language)
        # Possibility to put bad words filters here
        return char_val

    def clean_text_final(self, char):
        char_val = self.clean_char_eol(char)
        self.curr_text += [char_val]
        # Possibility to put bad words filters here
        self.prepare_text_buffer()
        return char_val

    def get_char_check_if_bad_text_redeemable(self, char, method_get):
        from .text_conversions import PokemonTextConversions
        if (not self.is_bad_text_redeemable) or self.has_encountered_eol or (not self.do_profanity_checks):
            return char

        to_check_text = self.last_text_converted.lower()
        words_redeemable = method_get(self.last_text_converted, self.language, self.is_curr_text_two_bytes)
        possible_continuations = set()

        if to_check_text in words_redeemable:
            possible_continuations.add('\0')

        for word in words_redeemable:
            if word != to_check_text:
                if self.last_text_converted.isupper():
                    word = word.upper()
                possible_continuations.add(word[len(self.last_text_converted)])

        converted_possible_continuations = []
        for possible_char in possible_continuations:
            converted_char = PokemonTextConversions.convert_char_to_genx_char(possible_char, self.reference_gen, self.language, do_two_bytes_only = self.is_curr_text_two_bytes)
            if (len(converted_char) == 1) and self.is_curr_text_two_bytes and (self.last_considered_char is not None):
                continue
            if self.is_curr_text_two_bytes and (self.last_considered_char is not None) and (self.last_considered_char != converted_char[0]):
                continue
            if self.last_considered_char is not None:
                converted_possible_continuations += [converted_char[1]]
            else:
                converted_possible_continuations += [converted_char[0]]

        # Default to the first one...
        if char not in converted_possible_continuations:
            char = self.utils_class.end_of_line
            # HOW COULD THIS NOT HAPPEN?!
            if len(converted_possible_continuations) > 0:
                char = converted_possible_continuations[0]

        return char

    def get_char_check_if_bad_text(self, char, method_is, method_get, max_name_len):
        from .text_conversions import PokemonNamesForGen, PokemonBadWordsFilter
        char = self.get_char_check_if_bad_text_redeemable(char, method_get)

        if (len(self.last_text_converted) <= 0) or (self.is_curr_text_two_bytes and (self.last_considered_char is None)) or self.has_encountered_eol or (not self.do_profanity_checks):
            return char

        next_text = PokemonNamesForGen.convert_generic_name_general_for_gen(self.curr_text + [char], self.reference_gen, language=self.language)
        if not PokemonBadWordsFilter.is_bad_word(next_text):
            return char

        # Avoid temporary false positives that can become legal with a next character...
        # Use max_name_len to check that one more character can be added...
        if (char != self.utils_class.end_of_line) and (len(self.curr_text + [char]) < max_name_len) and (not PokemonBadWordsFilter.is_bad_word(next_text + "?")):
            return char

        if method_is(self.last_text_converted, self.language, self.is_curr_text_two_bytes):
            if not self.is_bad_text_redeemable:
                self.is_bad_text_redeemable = True
                char = self.get_char_check_if_bad_text_redeemable(char, method_get)
        else:
            char = self.question_mark
            if (self.language == PokemonNamesForGen.KOREAN_LANGUAGE) and self.is_curr_text_two_bytes: # Hard to salvage, tbh...
                char = self.question_mark_kor[1]

        return char

    def handle_special_text(self, char):
        if (not self.is_korean_special) and (not self.is_patched_for_korean_special):
            return [char]

        if char == self.utils_class.prohibited_char_replacement:
            char = self.utils_class.prohibited_char
        self.special_chars_list += [char]

        if self.is_patched_for_korean_special:
            return self.utils_class.apply_text_transform_protect_korean_from_jpn_special(self.utils_class, self.special_chars_list)

        if self.is_korean_special:
            return self.utils_class.apply_text_transform_protect_international_from_korean_special(self.utils_class, self.special_chars_list, self)

        return [char]

    def process_and_clean_replacable_text(self, actual_char, do_name_replacement, replacement_name, method_is, method_get, max_name_len):
        curr_pos = len(self.curr_text)
        if do_name_replacement:
            if curr_pos < len(replacement_name):
                actual_char = replacement_name[curr_pos]
            else:
                actual_char = self.utils_class.end_of_line

        actual_char = self.get_char_check_if_bad_text(actual_char, method_is, method_get, max_name_len)

        return self.clean_text(actual_char)

    def process_and_clean_replacable_text_mon(self, actual_char, do_name_replacement, replacement_name):
        from .text_conversions import PokemonNamesForGen, PokemonBadWordsFilter
        return self.process_and_clean_replacable_text(actual_char, do_name_replacement, replacement_name, PokemonBadWordsFilter.get_is_root_whitelisted_of_mon_name, PokemonBadWordsFilter.get_root_whitelisted_words_of_mon_name, PokemonNamesForGen.get_pokemon_max_nickname_length(self.reference_gen, self.language))

    def process_and_clean_replacable_text_ot(self, actual_char, do_name_replacement, replacement_name):
        from .text_conversions import PokemonNamesForGen, PokemonBadWordsFilter
        return self.process_and_clean_replacable_text(actual_char, do_name_replacement, replacement_name, PokemonBadWordsFilter.get_is_root_whitelisted_of_ot_name, PokemonBadWordsFilter.get_root_whitelisted_words_of_ot_name, PokemonNamesForGen.get_trainer_max_name_length(self.reference_gen, self.language))

    def clean_text_partner(self, char, set_check_for_special_chars = False):
        from .text_conversions import PokemonNamesForGen
        trainer_name = PokemonNamesForGen.get_trainer_name_for_gen(self.reference_gen, language=self.language)

        self.do_special_chars_check = set_check_for_special_chars
        chars_to_process = self.handle_special_text(char)
        out_values = []

        for i in range(len(chars_to_process)):
            do_name_replacement = self.set_default_partner or self.force_default_name
            out_values += [self.process_and_clean_replacable_text_ot(chars_to_process[i], do_name_replacement, trainer_name)]

        if len(chars_to_process) == 1:
            return out_values[0]
        return out_values

    def clean_text_partner_special_char_check(self, char):
        return self.clean_text_partner(char, set_check_for_special_chars = True)

    def clean_text_partner_maybe_final(self, char):
        if not self.is_curr_text_two_bytes:
            return self.clean_text_partner_final(char)
        return self.clean_text_partner(char)

    def clean_text_partner_final(self, char):
        return self.clean_text_final(char)

    def clean_text_nickname(self, char, set_check_for_special_chars = False):
        from .text_conversions import PokemonNamesForGen
        self.last_species_nickname = self.curr_species_nickname
        mon_species = self.species_list[self.curr_species_nickname]
        is_an_egg = self.is_egg(self.curr_species_nickname)
        pokemon_name = None
        if (mon_species != self.free_value_species) and (mon_species != self.empty_value_species):
            if is_an_egg:
                pokemon_name = PokemonNamesForGen.get_egg_name_for_gen(self.reference_gen, language=self.language)
            else:
                pokemon_name = PokemonNamesForGen.get_pokemon_name_for_gen(mon_species, self.reference_gen, language=self.language)

        self.do_special_chars_check = set_check_for_special_chars
        chars_to_process = self.handle_special_text(char)
        out_values = []
        #print(chars_to_process)

        for i in range(len(chars_to_process)):
            do_name_replacement = (mon_species != self.free_value_species) and (mon_species != self.empty_value_species) and (pokemon_name is not None) and ((is_an_egg and self.do_sanity_checks) or self.set_default_nickname or self.force_default_name)
            out_values += [self.process_and_clean_replacable_text_mon(chars_to_process[i], do_name_replacement, pokemon_name)]

        if len(chars_to_process) == 1:
            return out_values[0]
        return out_values

    def clean_text_nickname_special_char_check(self, char):
        return self.clean_text_nickname(char, set_check_for_special_chars = True)

    def clean_text_nickname_final(self, char):
        if self.last_species_nickname == self.curr_species_nickname:
            self.curr_species_nickname += 1
        return self.clean_text_final(char)

    def clean_text_ot(self, char, set_check_for_special_chars = False):
        from .text_conversions import PokemonNamesForGen
        self.last_species_ot = self.curr_species_ot
        trainer_name = PokemonNamesForGen.get_trainer_name_for_gen(self.reference_gen, language=self.language)

        self.do_special_chars_check = set_check_for_special_chars
        chars_to_process = self.handle_special_text(char)
        out_values = []
        #print(chars_to_process)

        for i in range(len(chars_to_process)):
            # Extra check compared to trade/battle partner...
            if (chars_to_process[i] == self.trainer_name_id) and (len(self.curr_text) == 0):
                # "TRAINER" does not exist as a character in Korean
                from .text_conversions import PokemonNamesForGen
                if (self.language == PokemonNamesForGen.KOREAN_LANGUAGE) and self.do_sanity_checks:
                    self.force_default_name = True

            do_name_replacement = self.set_default_partner or self.force_default_name
            out_values += [self.process_and_clean_replacable_text_ot(chars_to_process[i], do_name_replacement, trainer_name)]

        if len(chars_to_process) == 1:
            return out_values[0]
        return out_values

    def clean_text_ot_mail_start(self, char):
        self.is_mail_ot = True
        return self.clean_text_ot(char)

    def clean_text_ot_special_char_check(self, char):
        return self.clean_text_ot(char, set_check_for_special_chars = True)

    def clean_text_ot_maybe_final(self, char):
        if not self.is_curr_text_two_bytes:
            return self.clean_text_ot_final(char)
        return self.clean_text_ot(char)

    def clean_text_ot_final(self, char):
        if self.last_species_ot == self.curr_species_ot:
            self.curr_species_ot += 1
        return self.clean_text_final(char)

    def clean_text_ot_final_no_end(self, char):
        # Needed for Japanese OTs
        if self.last_species_ot == self.curr_species_ot:
            self.curr_species_ot += 1
        return self.clean_text_final_no_end(char)

    def clean_text_ot_maybe_final_no_end(self, char):
        # Needed for Korean Mail OTs
        if not self.is_curr_text_two_bytes:
            return self.clean_text_ot_final(char)
        if self.last_species_ot == self.curr_species_ot:
            self.curr_species_ot += 1
        return self.clean_text_final_no_end(char)

    @clean_check_sanity_checks
    def check_mail_char_eol_newline(self, char):
        from .text_conversions import PokemonNamesForGen
        if (len(self.curr_text) == 0) or self.has_encountered_eol or (not self.do_mail_newline_checks):
            return char
        lines_to_process = self.utils_class.get_general_string_ready_for_counting_lines_and_chars(self.last_text_converted)
        num_chars_currline = len(lines_to_process[-1])
        num_lines = len(lines_to_process)
        if num_chars_currline >= self.max_mail_line_length:
            if num_lines == 1:
                if self.language == PokemonNamesForGen.KOREAN_LANGUAGE:
                    char = self.newline_kor
                else:
                    char = self.newline
            else:
                char = self.utils_class.end_of_line
        return char

    def clean_text_mail(self, char):
        from .text_conversions import PokemonNamesForGen
        # Mails allow different characters...
        self.is_mail = True
        char = self.check_mail_char_eol_newline(char)
        added_newline = False
        # Korean mail MUST be two bytes long...
        # Otherwise bad stuff happens...
        #if self.language == PokemonNamesForGen.KOREAN_LANGUAGE:
        #    self.is_curr_text_two_bytes = True
        if (self.language == PokemonNamesForGen.KOREAN_LANGUAGE) and (not self.has_encountered_newline) and (char == self.utils_class.end_of_line) and self.do_sanity_checks and self.do_mail_newline_checks:
            char = self.newline_kor
            added_newline = True
        out_val = self.clean_text(char)
        if added_newline:
            self.force_next_eol = True
        return out_val

    # Ensures a newline is present at the fixed position.
    # For most mails, this sets the newline. Even if they end
    # early. For the KENYA mail, it won't (as expected).
    def clean_text_mail_check_newline_int(self, char):
        from .text_conversions import PokemonNamesForGen
        if (self.language != PokemonNamesForGen.KOREAN_LANGUAGE) and (not self.has_encountered_newline) and self.do_sanity_checks:
            char = self.newline
        return self.clean_text_mail(char)

    def clean_text_mail_check_newline_kor_final_int(self, char):
        from .text_conversions import PokemonNamesForGen
        if self.language != PokemonNamesForGen.KOREAN_LANGUAGE:
            return self.clean_text_mail_final(char)
        if (not self.has_encountered_newline) and self.do_sanity_checks:
            char = self.newline_kor
        return self.clean_text_mail(char)

    def clean_text_mail_final(self, char):
        self.is_mail = True
        char = self.check_mail_char_eol_newline(char)
        return self.clean_text_final_no_end(char)

    def clean_text_newline(self, char):
        char_val = self.newline
        self.curr_text += [char_val]
        # Possibility to put bad words filters here
        return char_val

    def clean_text_final_no_end(self, char):
        char_val = self.clean_text_value(char, self.is_char_valid)
        self.curr_text += [char_val]
        # Possibility to put bad words filters here
        self.prepare_text_buffer()
        return char_val
    
    @clean_check_sanity_checks
    def clean_type(self, typing):
        return typing

    def check_range(self, stat_range, curr_stat):
        if curr_stat > stat_range[1]:
            curr_stat = stat_range[1]
        if curr_stat < stat_range[0]:
            curr_stat = stat_range[0]
        return curr_stat
    
    @clean_check_sanity_checks
    def check_stat(self, val, zero_min=False, zero_max=False):
        if self.curr_pos == 0:
            self.stat = 0
            min_stat = self.utils_class.stat_calculation(self.curr_stat_id, self.curr_species, self.iv, self.stat_exp, self.level, self.utils_class, do_exp=False)
            max_stat = self.utils_class.stat_calculation(self.curr_stat_id, self.curr_species, self.iv, self.stat_exp, self.level, self.utils_class)
            if zero_min or zero_max:
                min_stat = 0
            if zero_max:
                max_stat = 0
            self.stat_range = [min_stat, max_stat]
        curr_read_val = val << (8 * (1 - (self.curr_pos & 1)))
        self.stat = self.check_range(self.stat_range, (self.stat & 0xFF00) | curr_read_val)
        val = (self.stat >> (8 * (1 - (self.curr_pos & 1)))) & 0xFF
        self.curr_pos += 1
        if self.curr_pos >= 2:
            self.curr_stat_id += 1
            self.curr_pos = 0
        return val

    def is_egg(self, index):
        if self.species_list[index] == self.utils_class.egg_id:
            return True
        return False
    
    @clean_check_sanity_checks
    def check_hp(self, val):
        start_zero = False
        max_zero = False
        if self.curr_hp == 0:
            start_zero = True
            max_zero = self.is_egg(self.curr_species_pos-1)
        val = self.check_stat(val, zero_min=start_zero, zero_max=max_zero)
        if self.curr_pos == 0:
            if self.curr_hp == 0:
                self.hps = [0,0]
                self.curr_stat_id -= 1
            self.hps[self.curr_hp] = self.stat
            self.curr_hp += 1
            if self.curr_hp == 2:
                if self.hps[0] > self.hps[1]:
                    #Can put a warning for bad data
                    pass
        return val
        
    @clean_check_sanity_checks
    def clean_egg_cycles_friendship(self, cycles_friendship):
        return cycles_friendship
    
    def check_patch_set(self, val, patch_sets):
        if self.curr_patch_set >= len(patch_sets):
            return self.no_conversion_patch
        if val == self.end_of_patch:
            self.curr_patch_set += 1
            return val
        if GSCUtilsMisc.check_normal_list(patch_sets[self.curr_patch_set], val):
            return val
        return self.no_conversion_patch
    
    @clean_check_sanity_checks
    def clean_pokemon_patch_set(self, val):
        return self.check_patch_set(val, self.pokemon_patch_sets)
    
    @clean_check_sanity_checks
    def clean_mail_patch_set(self, val):
        return self.check_patch_set(val, self.mail_patch_set)
    
    @clean_check_sanity_checks
    def clean_japanese_mail_patch_set(self, val):
        return self.check_patch_set(val, self.japanese_mail_patch_set)
    
    def clean_value(self, value, checker, default_value):
        if checker(value):
            return value
        return default_value

    @clean_check_sanity_checks
    def clean_text_value(self, value, checker):
        from .text_conversions import PokemonNamesForGen
        if self.force_next_eol:
            self.force_next_eol = False
            value = self.utils_class.end_of_line

        was_last_partial = self.last_considered_char is not None

        # Apply changes as Korean has a couple of extra non-valid characters
        # that are valid in Japanese...
        dict_to_replace_bad_chars = self.utils_class.bad_ids_text_special_to_kor
        if self.language == PokemonNamesForGen.JAPANESE_LANGUAGE:
            dict_to_replace_bad_chars = self.utils_class.bad_ids_text_special_from_kor
        # Avoid getting the second byte of Korean chars caught in this, though.
        if (not was_last_partial) and (value in dict_to_replace_bad_chars.keys()) and (not self.has_encountered_eol):
            value = dict_to_replace_bad_chars[value]

        if checker(value):
            return value

        if self.is_mail:
            if (value == self.mail_text_null) and (not self.is_curr_text_two_bytes):
                return self.mail_text_null
            if (((value == self.newline) and (not self.is_curr_text_two_bytes)) or (value == self.newline_kor)) and (not self.has_encountered_newline):
                self.has_encountered_newline = True
                self.last_two_bytes_error = False
                if self.language == PokemonNamesForGen.KOREAN_LANGUAGE:
                    if self.is_curr_text_two_bytes is None:
                        self.is_curr_text_two_bytes = True
                    return self.newline_kor
                return self.newline
            # We only end up here in case of an error...
            # Also works well as error handling if bad data
            # is thrown at this...
            if self.language != PokemonNamesForGen.JAPANESE_LANGUAGE:
                if (value == self.mail_replaced_fe) or (value == self.mail_replaced_fe_kor):
                    if self.language == PokemonNamesForGen.KOREAN_LANGUAGE:
                        return self.mail_replaced_fe_kor
                    return self.mail_replaced_fe

        # Error handling - One byte
        if not self.is_curr_text_two_bytes:
            return self.question_mark

        # Error handling - Two bytes
        bytes_out = None
        index_out = 0

        if self.language == PokemonNamesForGen.KOREAN_LANGUAGE:
            bytes_out = self.question_mark_kor

        # How?!
        if bytes_out is None:
            return self.question_mark

        if was_last_partial:
            # This may produce unexpected characters in some error cases,
            # however there is no way to change an "already transmitted byte",
            # so this will have to do...
            # At least it won't display garbage...
            index_out = 1
            self.last_considered_char = None
        else:
            index_out = 0
            # Needed to ensure the next one selected will be the "other byte"
            self.last_considered_char = bytes_out[index_out]

        return bytes_out[index_out]
    
    @valid_check_sanity_checks
    def is_team_size_valid(self, team_size):
        if team_size <= 0 or team_size > 6:
            return False
        return True
    
    @valid_check_sanity_checks
    def is_item_valid(self, item):
        return not GSCUtilsMisc.check_normal_list(self.bad_ids_items, item)
    
    @valid_check_sanity_checks
    def is_move_valid(self, move):
        return not GSCUtilsMisc.check_normal_list(self.bad_ids_moves, move)
    
    @valid_check_sanity_checks
    def is_species_valid(self, species):
        return not GSCUtilsMisc.check_normal_list(self.bad_ids_pokemon, species)

    def convert_char_to_general(self, char):
        from .text_conversions import PokemonTextConversions
        out_value, is_partial, is_question_mark = PokemonTextConversions.convert_genx_char_to_char(char, self.reference_gen, self.language, last_char = self.last_considered_char)
        self.last_considered_char = None
        if is_partial:
            self.last_considered_char = char
        # Specially handle "\n" elsewhere...
        # If it even is allowed...
        if out_value == "\n":
            return "?", False, True
        return out_value, is_partial, is_question_mark
    
    @valid_check_sanity_checks
    def is_char_valid(self, char):
        curr_text_len = len(self.curr_text)
        if curr_text_len == 0:
            self.has_encountered_eol = False
            self.has_encountered_newline = False

        # Handle error protracting across two bytes
        if self.last_two_bytes_error:
            self.last_considered_char = None
            self.last_two_bytes_error = False
            return False

        # EOL is always allowed (provided it's not in a two-bytes setup)
        was_last_partial = self.last_considered_char is not None
        if (not was_last_partial) and (char == self.utils_class.end_of_line):
            # Prevent 0 length names...
            if (curr_text_len == 0) and (not self.is_mail):
                self.force_next_eol = True
                return False
            self.has_encountered_eol = True
            return True

        # After EOL, allow whatever...?
        if self.has_encountered_eol:
            # Ensure mail code can process the newline
            if self.is_mail and (not self.has_encountered_newline) and ((char == self.newline) or (char == self.newline_kor)):
                return False
            return True

        from .text_conversions import PokemonNamesForGen
        # Do this here, and keep the char as is elsewhere...
        # Make sure it matches with the language...
        # So elsewhere it can be fixed in case of mismatch...
        if self.is_mail and (self.language != PokemonNamesForGen.JAPANESE_LANGUAGE) and (((self.language != PokemonNamesForGen.KOREAN_LANGUAGE) and (char == self.mail_replaced_fe)) or ((self.language == PokemonNamesForGen.KOREAN_LANGUAGE) and (char == self.mail_replaced_fe_kor))):
            char = 0xFE

        # Do the actual conversion
        out_value, is_partial, is_question_mark = self.convert_char_to_general(char)

        if (char == self.trainer_name_id) and (curr_text_len == 0):
            # Prints TRAINER in all languages but Korean...
            # However it must be the first character, and followed by an EOL
            self.force_next_eol = True
            return True

        # Text is either fully two-bytes or fully single-bytes.
        # No mixing the two...
        if self.is_curr_text_two_bytes is None:
            self.is_curr_text_two_bytes = is_partial
        if (not self.is_curr_text_two_bytes) and is_partial:
            self.last_two_bytes_error = True
            return False
        if self.is_curr_text_two_bytes and (not is_partial) and (not was_last_partial):
            self.last_two_bytes_error = True
            return False

        if self.is_mail or self.is_mail_ot:
            # Avoid getting the second byte of Korean chars caught in this, though.
            # Mail data is special, as it technically should be checked against its own
            # language, instead of whatever the currently set language is...
            if (not self.use_strict_language_checks_mail) and (not was_last_partial):
                return not GSCUtilsMisc.check_normal_list(self.bad_ids_text, char)
        else:
            # Avoid getting the second byte of Korean chars caught in this, though.
            if (not self.use_strict_language_checks) and (not was_last_partial):
                return not GSCUtilsMisc.check_normal_list(self.bad_ids_text, char)

        # If there is nothing unexpected, return the value
        return not is_question_mark
