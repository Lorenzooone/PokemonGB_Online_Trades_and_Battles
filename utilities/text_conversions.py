import math
from .gsc_trading_data_utils import GSCUtilsMisc, GSCUtilsLoaders

text_conv_total_gens = 3

# Method to get pointer in a packed table from
# Pokémon Gen 3 to Gen X
def get_table_pointer_PG3TGX(table, entry):
    control_byte = table[0]
    size_initial_offset = (control_byte & 1) + 1
    size_offsets = ((control_byte >> 1) & 1) + 1
    offset_shifter = (control_byte >> 2) & 7
    offset_shifter_initial_offset = control_byte >> 5

    initial_offset = table[1] << offset_shifter_initial_offset
    offset_table_pos = 2
    if size_initial_offset == 2:
        initial_offset = GSCUtilsMisc.read_short_le(table, 2) << offset_shifter_initial_offset
        offset_table_pos = 4

    entries = (initial_offset - offset_table_pos) >> (size_offsets - 1)

    if entry >= entries:
        return None

    offset = table[offset_table_pos + entry] << offset_shifter
    if size_offsets == 2:
        offset = GSCUtilsMisc.read_short_le(table, offset_table_pos + (entry << 1)) << offset_shifter

    return initial_offset + offset

class PokemonSpeciesConversions:
    """
    Class which is used to convert the Pokémon species to/from the games.
    """
    LAST_VALID_GEN_2_MON = 251
    GEN2_EGG = 253
    GEN2_NO_MON = 255
    MR_MIME_SPECIES = 122
    UNOWN_SPECIES = 201
    DEOXYS_SPECIES = 410
    EGG_SPECIES = 412
    UNOWN_B_START = 415

    DEOXYS_FORMS_POS = 442
    UNOWN_REAL_NAME_POS = 445
    MR_MIME_OLD_NAME_POS = 446

    NUM_UNOWN_LETTERS_GEN3 = 28
    NUM_UNOWN_LETTERS_GEN2 = 26

    base_folder = "useful_data/text/"
    gen1_to_3_conv_table_path = "gen1_to_3_conv_table.bin"
    gen3_to_1_conv_table_path = "gen3_to_1_conv_table.bin"

    own_instance = None

    def __init__(self):
        self.gen1_to_3 = (GSCUtilsMisc.read_data(self.get_path(self.gen1_to_3_conv_table_path)))
        self.gen3_to_1 = (GSCUtilsMisc.read_data(self.get_path(self.gen3_to_1_conv_table_path)))
        PokemonSpeciesConversions.own_instance = self

    def get_path(self, target):
        return self.base_folder + target

    def get_self():
        if PokemonSpeciesConversions.own_instance is None:
            PokemonSpeciesConversions()
        return PokemonSpeciesConversions.own_instance

    def _convert_gen2_species_to_gen3(self, value, letter = 0, form = 0, is_for_nickname = False):
        if value == self.GEN2_EGG:
            return self.EGG_SPECIES
        if is_for_nickname:
            if value == self.MR_MIME_SPECIES:
                return self.MR_MIME_OLD_NAME_POS
            if value == self.UNOWN_SPECIES:
                return self.UNOWN_REAL_NAME_POS
        if (value == self.UNOWN_SPECIES) and (letter > 0) and (letter < self.NUM_UNOWN_LETTERS_GEN2):
            return self.UNOWN_B_START + letter - 1
        if value <= 0:
            return 0
        if value > self.LAST_VALID_GEN_2_MON:
            return 0
        return value

    def _convert_gen3_species_to_gen2(self, value):
        if value == self.MR_MIME_OLD_NAME_POS:
            value = self.MR_MIME_SPECIES
        if (value >= self.UNOWN_B_START) and (value < (self.UNOWN_B_START + self.NUM_UNOWN_LETTERS_GEN2)):
            return self.UNOWN_SPECIES
        if value <= 0:
            return 0
        if value > self.LAST_VALID_GEN_2_MON:
            return 0
        return value

    def _convert_gen1_species_to_gen3(self, value, letter = 0, form = 0, is_for_nickname = False):
        if value <= 0:
            return 0
        if value >= len(self.gen1_to_3):
            return 0
        out_value = self.gen1_to_3[value]
        if is_for_nickname:
            if out_value == self.MR_MIME_SPECIES:
                return self.MR_MIME_OLD_NAME_POS
        return out_value

    def _convert_gen3_species_to_gen1(self, value):
        if value == self.MR_MIME_OLD_NAME_POS:
            value = self.MR_MIME_SPECIES
        if value <= 0:
            return 0
        if value >= len(self.gen3_to_1):
            return 0
        return self.gen3_to_1[value]

    def _convert_gen2_species_to_gen1(self, value):
        return self._convert_gen3_species_to_gen1(self._convert_gen2_species_to_gen3(value))

    def _convert_gen1_species_to_gen2(self, value):
        return self._convert_gen3_species_to_gen2(self._convert_gen1_species_to_gen3(value))

    def convert_genx_species_to_geny(value, genx, geny, letter = 0, form = 0, is_for_nickname = False):
        if genx <= 0:
            return 0
        if genx > text_conv_total_gens:
            return 0
        if geny <= 0:
            return 0
        if geny > text_conv_total_gens:
            return 0

        self = PokemonSpeciesConversions.get_self()
        if genx == 1:
            if geny == 2:
                return self._convert_gen1_species_to_gen2(value)
            if geny == 3:
                return self._convert_gen1_species_to_gen3(value, letter=letter, form=form, is_for_nickname=is_for_nickname)
        if genx == 2:
            if geny == 1:
                return self._convert_gen2_species_to_gen1(value)
            if geny == 3:
                return self._convert_gen2_species_to_gen3(value, letter=letter, form=form, is_for_nickname=is_for_nickname)
        if genx == 3:
            if geny == 1:
                return self._convert_gen3_species_to_gen1(value)
            if geny == 2:
                return self._convert_gen3_species_to_gen2(value)
            if geny == 3:
                if is_for_nickname and (value == self.UNOWN_SPECIES):
                    return self.UNOWN_REAL_NAME_POS
        return value

class PokemonNamesForGen:
    """
    Class which is used to get Pokémon/Egg/Trainer names in the format
    of a specific game.
    """
    NUM_LANGUAGES = 8
    NUM_POKEMON_NAME_LANGUAGES = 4
    FIRST_VALID_LANGUAGE = 1
    FIRST_INTERNATIONAL_VALID_LANGUAGE = 2
    UNKNOWN_LANGUAGE = 0xFF
    JAPANESE_LANGUAGE = 1
    ENGLISH_LANGUAGE = 2
    FRENCH_LANGUAGE = 3
    ITALIAN_LANGUAGE = 4
    GERMAN_LANGUAGE = 5
    KOREAN_LANGUAGE = 6
    SPANISH_LANGUAGE = 7
    JAPANESE_LANGUAGE_STR = "Japanese"
    ENGLISH_LANGUAGE_STR = "English"

    NUM_GEN1_NAME_CHECKS = 256
    NUM_GEN2_NAME_CHECKS = 256
    NUM_GEN3_NAME_CHECKS = 447

    NAME_SIZE_INT = 11
    NAME_SIZE_OT_INT = 8
    NAME_SIZE_JP = 6
    NAME_SIZE_KOR_FILE = 10

    all_languages_list = [ENGLISH_LANGUAGE, JAPANESE_LANGUAGE, FRENCH_LANGUAGE, ITALIAN_LANGUAGE, GERMAN_LANGUAGE, KOREAN_LANGUAGE, SPANISH_LANGUAGE]
    sorted_languages_list = [JAPANESE_LANGUAGE, ENGLISH_LANGUAGE, FRENCH_LANGUAGE, ITALIAN_LANGUAGE, GERMAN_LANGUAGE, KOREAN_LANGUAGE, SPANISH_LANGUAGE]

    language_str_list = [JAPANESE_LANGUAGE_STR, ENGLISH_LANGUAGE_STR, "French", "Italian", "German", "Korean", "Spanish"]
    language_str_short_list = ["JPN", "ENG", "FRE", "ITA", "GER", "KOR", "SPA"]
    # From the Pokémon cartridge labels...
    language_str_short_list_alt = ["JPN", "USA", "FRA", "ITA", "NDE", "KOR", "ESP"]
    # Used in mail data from GSC. J, E, and K are added in...
    language_str_short_list_small = ["J", "E", "F", "I", "G", "K", "S"]
    # Extra, for easier initial recognition. Not for mail
    language_str_short_list_small_alt = ["J", "U", "F", "I", "D", "K", "S"]

    LANGUAGE_STRINGS_LIST = [language_str_list, language_str_short_list, language_str_short_list_alt, language_str_short_list_small, language_str_short_list_small_alt]

    base_folder = "useful_data/text/"
    pokemon_names_path = "pokemon_names.bin"
    language_names_index_path = "language_names_index.bin"
    pokemon_names_kr_gen2_path = "pokemon_names_kr_gen2.bin"
    egg_names_path = "egg_names.bin"
    egg_name_kr_gen2_path = "egg_name_kr_gen2.bin"
    trainer_names_path = "trainer_names.bin"
    trainer_name_kr_gen2_path = "trainer_name_kr_gen2.bin"

    own_instance = None

    def __init__(self):
        pokemon_names = (GSCUtilsMisc.read_data(self.get_path(self.pokemon_names_path)))
        language_names_index = (GSCUtilsMisc.read_data(self.get_path(self.language_names_index_path)))
        pokemon_names_kr_gen2 = (GSCUtilsMisc.read_data(self.get_path(self.pokemon_names_kr_gen2_path)))
        egg_names = (GSCUtilsMisc.read_data(self.get_path(self.egg_names_path)))
        egg_name_kr_gen2 = (GSCUtilsMisc.read_data(self.get_path(self.egg_name_kr_gen2_path)))
        trainer_names = (GSCUtilsMisc.read_data(self.get_path(self.trainer_names_path)))
        trainer_name_kr_gen2 = (GSCUtilsMisc.read_data(self.get_path(self.trainer_name_kr_gen2_path)))

        num_name_checks = [self.NUM_GEN1_NAME_CHECKS, self.NUM_GEN2_NAME_CHECKS, self.NUM_GEN3_NAME_CHECKS]
        self.pokemon_names = []
        for i in range(self.NUM_LANGUAGES):
            self.pokemon_names += [self.get_all_pokemon_names_for_language(pokemon_names, i, language_names_index)]
        self.replace_korean_pokemon_names(pokemon_names_kr_gen2)

        self.trainer_names = []
        for i in range(self.NUM_LANGUAGES):
            self.trainer_names += [self.get_name_for_language(trainer_names, i)]
        self.replace_korean_name(self.trainer_names, trainer_name_kr_gen2)

        self.egg_names = []
        for i in range(self.NUM_LANGUAGES):
            self.egg_names += [self.get_name_for_language(egg_names, i)]
        self.replace_korean_name(self.egg_names, egg_name_kr_gen2)

        PokemonNamesForGen.own_instance = self

    def get_path(self, target):
        return self.base_folder + target

    def get_self():
        if PokemonNamesForGen.own_instance is None:
            PokemonNamesForGen()
        return PokemonNamesForGen.own_instance

    def get_all_pokemon_names_for_language(self, pokemon_names, language, language_names_index):
        if language < 0:
            return None
        if language >= len(language_names_index):
            return None
        language_gen3_index = language_names_index[language]
        num_name_checks = [self.NUM_GEN1_NAME_CHECKS, self.NUM_GEN2_NAME_CHECKS, self.NUM_GEN3_NAME_CHECKS]
        out_pokemon_names = []
        for i in range(text_conv_total_gens):
            out_pokemon_names += [dict()]
            gen = i + 1
            for j in range(num_name_checks[i]):
                corresponding_index_gen3 = PokemonSpeciesConversions.convert_genx_species_to_geny(j, gen, 3, is_for_nickname = True)
                if corresponding_index_gen3 == 0:
                    continue
                pos_name = get_table_pointer_PG3TGX(pokemon_names, (corresponding_index_gen3 * self.NUM_POKEMON_NAME_LANGUAGES) + language_gen3_index)
                pokemon_name = self.extract_name_from_gen3_data(pokemon_names, pos_name, gen, language == self.JAPANESE_LANGUAGE)
                if pokemon_name is not None:
                    out_pokemon_names[i][j] = pokemon_name
        return out_pokemon_names

    def replace_korean_pokemon_names(self, pokemon_names_kr_gen2):
        for i in range(2):
            gen = i + 1
            old_dict = self.pokemon_names[self.KOREAN_LANGUAGE][i]
            self.pokemon_names[self.KOREAN_LANGUAGE][i] = dict()
            new_dict = self.pokemon_names[self.KOREAN_LANGUAGE][i]
            for mon_index in old_dict.keys():
                converted_index = mon_index
                if gen == 1:
                    converted_index = PokemonSpeciesConversions.convert_genx_species_to_geny(mon_index, gen, 2)
                new_dict[mon_index] = self.copy_gen2_name_to_array(pokemon_names_kr_gen2, self.NAME_SIZE_KOR_FILE * converted_index, self.NAME_SIZE_KOR_FILE)

    def replace_korean_name(self, names, kr_data_gen2):
        for i in range(2):
            names[self.KOREAN_LANGUAGE][i] = self.copy_gen2_name_to_array(kr_data_gen2, 0, len(kr_data_gen2))

    def get_name_for_language(self, names_data, language):
        if language < 0:
            return None
        if language >= self.NUM_LANGUAGES:
            return None
        out_names = []
        for i in range(text_conv_total_gens):
            gen = i + 1
            out_names += [None]
            pos_name = get_table_pointer_PG3TGX(names_data, language)
            actual_name = self.extract_name_from_gen3_data(names_data, pos_name, gen, language == self.JAPANESE_LANGUAGE)
            if actual_name is not None:
                out_names[i] = actual_name
        return out_names

    def extract_name_from_gen3_data(self, data, offset, gen, is_jp):
        if offset is None:
            return None
        if gen <= 0:
            return None
        if gen > text_conv_total_gens:
            return None

        max_name_size = self.NAME_SIZE_INT
        if is_jp:
            max_name_size = self.NAME_SIZE_JP
        conversion_method = PokemonTextConversions.convert_gen3_char_to_gen12_char
        post_end_char = None
        if gen == 3:
            conversion_method = None
            post_end_char = 0

        out_name = []
        for k in range(max_name_size):
            in_char = data[offset + k]
            out_char = in_char
            if conversion_method is not None:
                out_char = conversion_method(in_char, is_jp = is_jp, to_jp = is_jp)
            out_name += [out_char]
            if PokemonTextConversions.is_gen3_eol(in_char):
                if post_end_char is None:
                    post_end_char = out_char
                while k < (max_name_size - 1):
                    out_name += [post_end_char]
                    k += 1
                break
        return out_name

    def copy_gen2_name_to_array(self, data, offset, size_data, is_jp = False):
        out_array = []
        max_name_size = self.NAME_SIZE_INT
        if is_jp:
            max_name_size = self.NAME_SIZE_JP
        for i in range(size_data):
            out_array += [data[offset + i]]
            if i == (size_data - 1):
                while i < (max_name_size - 1):
                    out_array += [PokemonTextConversions.GEN2_EOL]
                    i += 1
        return out_array

    def get_generic_name_for_gen(self, data, gen, language = ENGLISH_LANGUAGE):
        if gen <= 0:
            return None
        if gen > text_conv_total_gens:
            return None
        if language < 0:
            return None
        if language >= self.NUM_LANGUAGES:
            return None
        return data[language][gen - 1]

    def get_pokemon_name_for_gen(species, gen, language = ENGLISH_LANGUAGE):
        self = PokemonNamesForGen.get_self()
        selected_dict = self.get_generic_name_for_gen(self.pokemon_names, gen, language=language)
        if selected_dict is None:
            return None
        species_real = PokemonSpeciesConversions.convert_genx_species_to_geny(species, gen, gen, is_for_nickname = True)
        if species_real not in selected_dict.keys():
            return None
        return selected_dict[species_real]

    def get_trainer_name_for_gen(gen, language = ENGLISH_LANGUAGE):
        self = PokemonNamesForGen.get_self()
        return self.get_generic_name_for_gen(self.trainer_names, gen, language=language)

    def get_egg_name_for_gen(gen, language = ENGLISH_LANGUAGE):
        self = PokemonNamesForGen.get_self()
        return self.get_generic_name_for_gen(self.egg_names, gen, language=language)

    def convert_generic_name_general_for_gen(curr_list, gen, language = ENGLISH_LANGUAGE):
        if curr_list is None:
            return ""
        if (language == PokemonNamesForGen.KOREAN_LANGUAGE) and ((gen == 1) or (gen == 2)):
            return PokemonNamesForGen.convert_korean_name_general_for_gen12(curr_list)
        out_str = ""
        conv_method = PokemonTextConversions.convert_gen12_char_to_char
        eol_method = PokemonTextConversions.is_gen12_eol
        if gen == 3:
            eol_method = PokemonTextConversions.is_gen3_eol
            conv_method = PokemonTextConversions.convert_gen3_char_to_char
        for i in range(len(curr_list)):
            if eol_method(curr_list[i]):
                break
            out_str += conv_method(curr_list[i], is_jp=(language==PokemonNamesForGen.JAPANESE_LANGUAGE))
        return out_str

    def convert_korean_name_general_for_gen12(curr_list):
        if curr_list is None:
            return ""
        out_str = ""
        conv_method = PokemonTextConversions.convert_gen12_kor_char_to_char
        eol_method = PokemonTextConversions.is_gen12_eol
        i = 0
        while i < len(curr_list):
            if eol_method(curr_list[i]):
                break
            char_next = PokemonTextConversions.GEN2_EOL # How could this happen without cheats?! But still be safe...
            if (i + 1) < len(curr_list):
                char_next = curr_list[i + 1]
            out_combo = conv_method(curr_list[i], char_next)
            i += out_combo[0]
            out_str += out_combo[1]
        return out_str

    def get_pokemon_name_general_for_gen(species, gen, language = ENGLISH_LANGUAGE):
        curr_list = PokemonNamesForGen.get_pokemon_name_for_gen(species, gen, language=language)
        return PokemonNamesForGen.convert_generic_name_general_for_gen(curr_list, gen, language=language)

    def get_method_name_general_for_gen(method, gen, language = ENGLISH_LANGUAGE):
        curr_list = method(gen, language=language)
        return PokemonNamesForGen.convert_generic_name_general_for_gen(curr_list, gen, language=language)

    def get_egg_name_general_for_gen(gen, language = ENGLISH_LANGUAGE):
        return PokemonNamesForGen.get_method_name_general_for_gen(PokemonNamesForGen.get_egg_name_for_gen, gen, language=language)

    def get_trainer_name_general_for_gen(gen, language = ENGLISH_LANGUAGE):
        return PokemonNamesForGen.get_method_name_general_for_gen(PokemonNamesForGen.get_trainer_name_for_gen, gen, language=language)

    def get_trainer_max_name_length(gen, language):
        language_max_length_ot_jpn = 5
        language_max_length_ot_int = 7
        language_max_length_ot_kor = 10

        if language == PokemonNamesForGen.KOREAN_LANGUAGE:
            return language_max_length_ot_kor

        if language == PokemonNamesForGen.JAPANESE_LANGUAGE:
            return language_max_length_ot_jpn

        return language_max_length_ot_int

    def get_pokemon_max_nickname_length(gen, language):
        language_max_length_nick_jpn = 5
        language_max_length_nick_int = 10

        if language == PokemonNamesForGen.JAPANESE_LANGUAGE:
            return language_max_length_nick_jpn

        return language_max_length_nick_int

class PokemonTextConversions:
    """
    Class which is used to convert the text to/from the games.
    """
    GEN3_EOL = 0xFF
    GEN2_EOL = 0x50
    GENERIC_EOL = 0
    GENERIC_EOL_2 = '\0'

    GEN3_QUESTION = 0xAC
    GEN2_QUESTION = 0xE6
    GENERIC_QUESTION = 0x3F

    GEN2_NEWLINE_INT = 0x4E
    GEN2_NEWLINE_KOR = 0x59

    base_folder = "useful_data/text/"
    text_gen3_gen12_int_path = "text_gen3_to_gen12_int.bin"
    text_gen3_gen12_int_jp_path = "text_gen3_to_gen12_int_jp.bin"
    text_gen3_gen12_jp_path = "text_gen3_to_gen12_jp.bin"
    text_gen3_gen12_jp_int_path = "text_gen3_to_gen12_jp_int.bin"
    text_gen3_general_int_path = "text_gen3_to_general_int.txt"
    text_gen3_general_jp_path = "text_gen3_to_general_jp.txt"
    text_gen2_general_kor_path = "text_gen2_to_general_kor.txt"
    text_gen12_gen3_int_path = "text_gen12_to_gen3_int.bin"
    text_gen12_gen3_jp_path = "text_gen12_to_gen3_jp.bin"
    text_general_gen3_int_path = "text_general_to_gen3_int.bin"
    text_general_gen3_jp_path = "text_general_to_gen3_jp.bin"

    own_instance = None

    def __init__(self):
        self.gen3_gen12_int = (GSCUtilsMisc.read_data(self.get_path(self.text_gen3_gen12_int_path)))
        self.gen3_gen12_int_jp = (GSCUtilsMisc.read_data(self.get_path(self.text_gen3_gen12_int_jp_path)))
        self.gen3_gen12_jp = (GSCUtilsMisc.read_data(self.get_path(self.text_gen3_gen12_jp_path)))
        self.gen3_gen12_jp_int = (GSCUtilsMisc.read_data(self.get_path(self.text_gen3_gen12_jp_int_path)))
        self.gen3_general_int = self.parse_alphabet(GSCUtilsLoaders.read_text_file(self.get_path(self.text_gen3_general_int_path)))
        self.gen3_general_jp = self.parse_alphabet(GSCUtilsLoaders.read_text_file(self.get_path(self.text_gen3_general_jp_path)))
        self.gen2_general_kor = self.parse_alphabet(GSCUtilsLoaders.read_text_file(self.get_path(self.text_gen2_general_kor_path)))
        self.general_gen2_kor = self.reverse_parse_alphabet(self.gen2_general_kor)
        self.gen12_gen3_int = (GSCUtilsMisc.read_data(self.get_path(self.text_gen12_gen3_int_path)))
        self.gen12_gen3_jp = (GSCUtilsMisc.read_data(self.get_path(self.text_gen12_gen3_jp_path)))
        self.general_gen3_int = (GSCUtilsMisc.read_data(self.get_path(self.text_general_gen3_int_path)))
        self.general_gen3_jp = (GSCUtilsMisc.read_data(self.get_path(self.text_general_gen3_jp_path)))
        PokemonTextConversions.own_instance = self

    def get_path(self, target):
        return self.base_folder + target

    def parse_table(self, lines, table_rows, table_row_len, target = None):
        table_total = table_rows * table_row_len
        tables_found = []
        start = None
        has_started_search = target is None
        for i in range(len(lines)):
            processed_line = lines[i].replace("\n", "").replace("\r", "")
            if not has_started_search:
                has_started_search = processed_line.startswith("# TABLE " + str(target))
            else:
                if processed_line.startswith("#"):
                    continue
                if len(processed_line.strip()) == 0:
                    continue
                start = i
                break

        if start is None:
            return [[0] * table_total]

        out_table = []
        for i in range(table_rows):
            processed_line = lines[start + i].replace("\n", "").replace("\r", "").split("#")
            if len(processed_line) != (table_row_len + 1):
                return [[1] * table_total]
            for j in range(table_row_len):
                if (target is None) and (processed_line[j] == "<TABLE>"):
                    out_table += [[]]
                    tables_found += [(i * table_row_len) + j]
                else:
                    out_table += [processed_line[j]]

        return out_table, tables_found

    def parse_alphabet(self, lines):
        table_rows = 16
        table_row_len = 16
        out = self.parse_table(lines, table_rows, table_row_len)
        if len(out[1]) <= 0:
            return out[0]
        for subtable in out[1]:
            sub_out = self.parse_table(lines, table_rows, table_row_len, target = subtable)
            out[0][subtable] = sub_out[0]
        return out[0]

    def reverse_parse_alphabet(self, table, previous_value = [], curr_dict = None):
        is_top = len(previous_value) == 0
        if is_top:
            curr_dict = dict()
        for i in range(len(table)):
            item = table[i]
            if (isinstance(item, list) and (len(item) == len(table))) and is_top:
                self.reverse_parse_alphabet(item, previous_value = [i], curr_dict = curr_dict)
            elif item != "?":
                if item not in curr_dict.keys():
                    curr_dict[item] = []
                curr_dict[item] += [previous_value + [i]]
                if item == "<?>":
                    item = "?"
                    if item not in curr_dict.keys():
                        curr_dict[item] = []
                    curr_dict[item] += [previous_value + [i]]
        return curr_dict

    def get_self():
        if PokemonTextConversions.own_instance is None:
            PokemonTextConversions()
        return PokemonTextConversions.own_instance

    def convert_gen12_char_to_char(value, is_jp = False):
        self = PokemonTextConversions.get_self()
        if value == self.GEN2_EOL:
            return self.GENERIC_EOL
        if value == self.GEN2_NEWLINE_INT:
            return "\n"
        conv_table1 = self.gen12_gen3_int
        conv_table2 = self.gen3_general_int
        if is_jp:
            conv_table1 = self.gen12_gen3_jp
            conv_table2 = self.gen3_general_jp
        out = conv_table2[conv_table1[value]]
        if out == "<?>":
            out = "?"
        return out

    def convert_gen12_kor_char_to_char(value, value_next):
        self = PokemonTextConversions.get_self()
        table_used = self.gen2_general_kor
        if value == self.GEN2_EOL:
            return 1, self.GENERIC_EOL
        if value == self.GEN2_NEWLINE_INT:
            return 1, "\n"
        if value == self.GEN2_NEWLINE_KOR:
            return 1, "\n"
        out_value = table_used[value]
        if not (isinstance(out_value, list) and (len(out_value) == len(table_used))):
            if out_value == "<?>":
                out_value = "?"
            return 1, out_value
        if value_next is None:
            return 2, "<TABLE>"
        out_value = out_value[value_next]
        if out_value == "<?>":
            out_value = "?"
        return 2, out_value

    def convert_char_to_gen12_kor_char(value, num_wanted_out):
        self = PokemonTextConversions.get_self()
        table_used = self.general_gen2_kor
        if value == self.GENERIC_EOL:
            return [self.GEN2_EOL]
        if value not in table_used:
            return []
        out_value = table_used[value]
        for item in out_value:
            if len(item) == num_wanted_out:
                return item
        return []

    def convert_char_to_gen12_char(value, is_jp = False):
        self = PokemonTextConversions.get_self()
        if value == self.GENERIC_EOL:
            return self.GEN2_EOL
        conv_table1 = self.general_gen3_int
        conv_table2 = self.gen3_gen12_int
        if is_jp:
            conv_table1 = self.general_gen3_jp
            conv_table2 = self.gen3_gen12_jp
        out = conv_table2[conv_table1[ord(value)]]
        return out

    def convert_gen3_char_to_char(value, is_jp = False):
        self = PokemonTextConversions.get_self()
        if value == self.GEN3_EOL:
            return self.GENERIC_EOL
        conv_table = self.gen3_general_int
        if is_jp:
            conv_table = self.gen3_general_jp
        out = conv_table[value]
        if out == "<?>":
            out = "?"
        return out

    def convert_char_to_gen3_char(value, is_jp = False):
        self = PokemonTextConversions.get_self()
        if value == self.GENERIC_EOL:
            return self.GEN3_EOL
        conv_table = self.general_gen3_int
        if is_jp:
            conv_table = self.general_gen3_jp
        out = conv_table[ord(value)]
        return out

    def convert_gen3_char_to_gen12_char(value, is_jp = False, to_jp = False):
        self = PokemonTextConversions.get_self()
        if value == self.GEN3_EOL:
            return self.GEN2_EOL
        conv_table = self.gen3_gen12_int
        if is_jp:
            if to_jp:
                conv_table = self.gen3_gen12_jp
            else:
                conv_table = self.gen3_gen12_jp_int
        elif to_jp:
            conv_table = self.gen3_gen12_int_jp
        out = conv_table[value]
        return out

    def convert_gen12_char_to_gen3_char(value, is_jp = False):
        self = PokemonTextConversions.get_self()
        if value == self.GEN2_EOL:
            return self.GEN3_EOL
        conv_table = self.gen12_gen3_int
        if is_jp:
            conv_table = self.gen12_gen3_jp
        out = conv_table[value]
        return out

    def convert_genx_char_to_char(value, gen, language, last_char = None):
        is_partial = False
        if language is None:
            language = PokemonNamesForGen.ENGLISH_LANGUAGE
        if gen == 3:
            out_value = PokemonTextConversions.convert_gen3_char_to_char(value, language == PokemonNamesForGen.JAPANESE_LANGUAGE)
            is_eol = PokemonTextConversions.is_gen3_eol(value)
        else:
            if language == PokemonNamesForGen.KOREAN_LANGUAGE:
                if last_char is None:
                    out_value = PokemonTextConversions.convert_gen12_kor_char_to_char(value, None)
                    if out_value[1] == "<TABLE>":
                        is_partial = True
                else:
                    out_value = PokemonTextConversions.convert_gen12_kor_char_to_char(last_char, value)
                out_value = out_value[1]
            else:
                out_value = PokemonTextConversions.convert_gen12_char_to_char(value, language == PokemonNamesForGen.JAPANESE_LANGUAGE)
            is_eol = PokemonTextConversions.is_gen12_eol(value)
        if is_eol:
            return '\0', False, False
        return out_value, is_partial, out_value == '?'

    def convert_char_to_genx_char(value, gen, language, do_two_bytes_only = False):
        if language is None:
            language = PokemonNamesForGen.ENGLISH_LANGUAGE
        if PokemonTextConversions.is_generic_eol(value):
            if gen == 3:
                return [PokemonTextConversions.GEN3_EOL]
            return [PokemonTextConversions.GEN2_EOL]
        if gen == 3:
            out_value = [PokemonTextConversions.convert_char_to_gen3_char(value, language == PokemonNamesForGen.JAPANESE_LANGUAGE)]
        else:
            if (language == PokemonNamesForGen.KOREAN_LANGUAGE) and do_two_bytes_only:
                out_value = PokemonTextConversions.convert_char_to_gen12_kor_char(value, 2)
                if len(out_value) == 0:
                    out_value = PokemonTextConversions.convert_char_to_gen12_kor_char("?", 2)
            else:
                out_value = [PokemonTextConversions.convert_char_to_gen12_char(value, language == PokemonNamesForGen.JAPANESE_LANGUAGE)]
        return out_value

    def is_gen12_eol(value):
        self = PokemonTextConversions.get_self()
        return value == self.GEN2_EOL

    def is_gen3_eol(value):
        self = PokemonTextConversions.get_self()
        return value == self.GEN3_EOL

    def is_generic_eol(value):
        self = PokemonTextConversions.get_self()
        if value == self.GENERIC_EOL:
            return True
        return value == self.GENERIC_EOL_2

class PokemonBadWordsFilter:
    base_folder = "useful_data/text/"
    bad_words_replacement_list_path = "bad_words_replacement_list.txt"
    blacklisted_regexes_path = "blacklisted_regexes.bin"
    letters_blacklist_dict_path = "letters_blacklist_dict.txt"
    whitelisted_words_path = "whitelisted_words.txt"

    own_instance = None

    def __init__(self):

        self.bad_words_replacement_dict = dict()
        in_lines = GSCUtilsLoaders.read_text_file(self.get_path(self.bad_words_replacement_list_path))
        for line in in_lines:
            considered = line.replace("\n", "")
            items = considered.split(" ")
            if len(items) < 2:
                continue
            if items[0] in self.bad_words_replacement_dict.keys():
                print(items[0] + " DUPLICATED")
            self.bad_words_replacement_dict[items[0]] = items[1]

        in_lines = GSCUtilsLoaders.read_text_file(self.get_path(self.whitelisted_words_path))
        self.whitelisted_words = set()
        for line in in_lines:
            considered = line.replace("\n", "")
            if considered == "":
                continue
            self.whitelisted_words.add(considered)

        self.whitelisted_words_multiletters_jpn_kor = self._create_whitelisted_dict(PokemonNamesForGen.NAME_SIZE_JP - 1)
        self.whitelisted_words_multiletters_int_nickname = self._create_whitelisted_dict(PokemonNamesForGen.NAME_SIZE_INT - 1)
        self.whitelisted_words_multiletters_int_ot_name = self._create_whitelisted_dict(PokemonNamesForGen.NAME_SIZE_OT_INT - 1)

        # By default the list of bad regexes is obfuscated...
        # This is not done maliciously. It's done to avoid
        # having explicit words visible in the repo...
        in_data = GSCUtilsMisc.read_data(self.get_path(self.blacklisted_regexes_path))
        in_letters = GSCUtilsLoaders.read_text_file(self.get_path(self.letters_blacklist_dict_path))
        in_chars_dict = dict()

        # Get a replacement dict with the value that every letter corresponds to
        # Hopefully not randomizing the values does not come back to byte me...
        # Censored words list for Nintendo Switch 66, obtained from Bulbapedia
        for i in range(len(in_letters)):
            if len(in_letters[i]) == 0:
                continue
            items = in_letters[i].replace("\n", "").split("#")
            in_chars_dict[int(items[1])] = items[0]

        num_bytes = GSCUtilsMisc.from_n_bytes_le(in_data, 4)
        num_bytes_per_word = GSCUtilsMisc.from_n_bytes_le(in_data, 2, start = 4)
        linebreak = GSCUtilsMisc.from_n_bytes_le(in_data, num_bytes_per_word, start = 6)

        curr_pos = 8
        in_lines = []
        curr_line = ""

        # Use the replacement dict to recreate the regexes
        while curr_pos < num_bytes:
            curr_char = GSCUtilsMisc.from_n_bytes_le(in_data, num_bytes_per_word, start = curr_pos)
            curr_pos += num_bytes_per_word
            if curr_char == linebreak:
                if curr_line != "":
                    in_lines += [curr_line]
                    curr_line = ""
            elif curr_char in in_chars_dict.keys():
                curr_line += in_chars_dict[curr_char]

        # Create the giant regex used to check for bad words
        self.re_string = '(?:% s)' % '|'.join(in_lines)

        PokemonBadWordsFilter.own_instance = self

    def get_path(self, target):
        return self.base_folder + target

    def get_self():
        if PokemonBadWordsFilter.own_instance is None:
            PokemonBadWordsFilter()
        return PokemonBadWordsFilter.own_instance

    def _create_whitelisted_dict(self, max_size):
        whitelist_subset = set()
        for word in self.whitelisted_words:
            if len(word) <= max_size:
                whitelist_subset.add(word)
        dict_list = []
        for i in range(max_size + 1):
            dict_list += [dict()]
            for word in whitelist_subset:
                if i < len(word):
                    key = word[:i + 1]
                    if key not in dict_list[i]:
                        dict_list[i][key] = list()
                    dict_list[i][key] += [word]
        return dict_list

    def _get_root_whitelisted_words(word, dict_to_use):
        word_to_check = word.lower()
        word_len = len(word_to_check)
        dict_index = word_len - 1
        if (dict_index) < 0:
            return [""]
        if (dict_index) >= len(dict_to_use):
            return None
        if word_to_check in dict_to_use[dict_index].keys():
            return dict_to_use[dict_index][word_to_check]
        return None

    def get_root_whitelisted_words_of_mon_name(word, language, is_two_bytes):
        self = PokemonBadWordsFilter.get_self()
        dict_to_use = self.whitelisted_words_multiletters_int_nickname
        if language == PokemonNamesForGen.JAPANESE_LANGUAGE:
            dict_to_use = self.whitelisted_words_multiletters_jpn_kor
        if (language == PokemonNamesForGen.KOREAN_LANGUAGE) and is_two_bytes:
            dict_to_use = self.whitelisted_words_multiletters_jpn_kor
        return PokemonBadWordsFilter._get_root_whitelisted_words(word, dict_to_use)

    def get_root_whitelisted_words_of_ot_name(word, language, is_two_bytes):
        self = PokemonBadWordsFilter.get_self()
        dict_to_use = self.whitelisted_words_multiletters_int_ot_name
        if language == PokemonNamesForGen.JAPANESE_LANGUAGE:
            dict_to_use = self.whitelisted_words_multiletters_jpn_kor
        if (language == PokemonNamesForGen.KOREAN_LANGUAGE) and is_two_bytes:
            dict_to_use = self.whitelisted_words_multiletters_jpn_kor
        return PokemonBadWordsFilter._get_root_whitelisted_words(word, dict_to_use)

    def get_is_root_whitelisted_of_mon_name(word, language, is_two_bytes):
        return PokemonBadWordsFilter.get_root_whitelisted_words_of_mon_name(word, language, is_two_bytes) is not None

    def get_is_root_whitelisted_of_ot_name(word, language, is_two_bytes):
        return PokemonBadWordsFilter.get_root_whitelisted_words_of_ot_name(word, language, is_two_bytes) is not None

    def is_bad_word(word):
        import re
        self = PokemonBadWordsFilter.get_self()
        word_to_check = word.lower()

        if word_to_check in self.whitelisted_words:
            return False

        if re.match(self.re_string, word_to_check):
            return True

        for replacement_key in self.bad_words_replacement_dict.keys():
            word_to_check = word_to_check.replace(replacement_key, self.bad_words_replacement_dict[replacement_key])

        if re.match(self.re_string, word_to_check):
            return True

        return False
