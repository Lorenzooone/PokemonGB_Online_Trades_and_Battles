from .gsc_trading import GSCTrading
from .gsc_trading_data_utils import GSCUtilsLoaders, GSCUtilsMisc, GSCTradingMailData, GSCUtils
from .text_conversions import PokemonNamesForGen

class GSCJPMailConverter:
    """
    Class which handles converting the GSC Japanese mail data
    to the international format.
    """
    base_folder = "useful_data/gsc/"
    table_to_jp_path = "mail_conversion_table_en_to_jp.bin"
    table_to_int_path = "mail_conversion_table_jp_to_en.bin"
    mail_jp_checks_path = "mail_checks_jp.bin"
    chars_to_jp_eng_path = "mail_en_char_conv_table.bin"
    chars_to_jp_ger_fre_path = "mail_ger_fre_char_conv_table.bin"
    chars_to_jp_ita_spa_path = "mail_ita_spa_char_conv_table.bin"
    
    end_of_line = 0x50
    eol_kor_start_msg_data_replacement = 0x2C

    reference_gen = 2
    id_language_char = 0x63
    extra_distance_jp = 5
    extra_distance_int = 0xA
    ot_name_real_len_int = 7
    ot_name_real_len_jpn = 5
    language_sender_pos_int = 0x8
    jpn_message_len = 0x21
    sender_jpn_len = 0x09 # JPN: 5 for OT Name + 2 for OT ID + 1 for Mon + 1 for Mail type
    full_mail_jp_len = jpn_message_len + sender_jpn_len
    base_int_mail_len = 0x21
    base_kor_mail_len = 0x41
    mail_len = 0x41 # 0x21
    sender_int_len = 0xE
    mail_pos_jp = [
        (0*full_mail_jp_len),
        (1*full_mail_jp_len),
        (2*full_mail_jp_len),
        (3*full_mail_jp_len),
        (4*full_mail_jp_len),
        (5*full_mail_jp_len)
    ]
    mail_pos_int = [
        (0*mail_len),
        (1*mail_len),
        (2*mail_len),
        (3*mail_len),
        (4*mail_len),
        (5*mail_len)
    ]
    sender_pos_jp = [
        jpn_message_len + (0*full_mail_jp_len),
        jpn_message_len + (1*full_mail_jp_len),
        jpn_message_len + (2*full_mail_jp_len),
        jpn_message_len + (3*full_mail_jp_len),
        jpn_message_len + (4*full_mail_jp_len),
        jpn_message_len + (5*full_mail_jp_len)
    ]
    sender_pos_int = [
        (mail_len*6) + (0*sender_int_len),
        (mail_len*6) + (1*sender_int_len),
        (mail_len*6) + (2*sender_int_len),
        (mail_len*6) + (3*sender_int_len),
        (mail_len*6) + (4*sender_int_len),
        (mail_len*6) + (5*sender_int_len)
    ]

    def __init__(self, checks):
        self.utils_class = self.get_utils_class()
        self.conversion_functions = [
            self.do_zero,
            self.mail_conversion,
            self.sender_conversion,
            self.extra_conversion,
            self.do_ff,
            self.do_20,
            self.start_mail_conversion,
            self.do_eol,
            self.start_sender_conversion
        ]
        self.mail_conversion_table_jp = GSCUtilsLoaders.prepare_functions_map(GSCUtilsMisc.read_data(self.get_path(self.table_to_jp_path)), self.conversion_functions)
        self.mail_conversion_table_int = GSCUtilsLoaders.prepare_functions_map(GSCUtilsMisc.read_data(self.get_path(self.table_to_int_path)), self.conversion_functions)
        self.mail_checker = GSCUtilsLoaders.prepare_functions_map(GSCUtilsMisc.read_data(self.get_path(self.mail_jp_checks_path)), checks.check_functions)
        self.chars_to_jp_en_table = GSCUtilsMisc.read_data(self.get_path(self.chars_to_jp_eng_path))
        self.chars_to_jp_ger_fre_table = GSCUtilsMisc.read_data(self.get_path(self.chars_to_jp_ger_fre_path))
        self.chars_to_jp_ita_spa_table = GSCUtilsMisc.read_data(self.get_path(self.chars_to_jp_ita_spa_path))
        self.chars_from_jp_en_table = self.generate_reverse_dict_from_table(self.chars_to_jp_en_table)
        self.chars_from_jp_ger_fre_table = self.generate_reverse_dict_from_table(self.chars_to_jp_ger_fre_table)
        self.chars_from_jp_ita_spa_table = self.generate_reverse_dict_from_table(self.chars_to_jp_ita_spa_table)
        
    def get_utils_class(self):
        return GSCUtils
        
    def get_path(self, target):
        return self.base_folder + target

    def generate_reverse_dict_from_table(self, table):
        out = dict()
        for i in range(len(table)):
            elem = table[i]
            if (elem & 0x80) != 0:
                continue
            # Debug
            if elem in out.keys():
                print("DUPLICATED! " + str(elem))
            out[elem] = i
        return out

    def get_mail_language_from_int_provided(self, language_data):
        return GSCTradingMailData.get_int_mail_data_language(language_data, self.reference_gen)

    def get_mail_language_from_int_mail_data(self, message_data, author_data):
        return self.get_mail_language_from_int_provided(author_data[self.language_sender_pos_int : self.language_sender_pos_int + 2])

    def get_mail_language_from_int(self, data, index):
        return self.get_mail_language_from_int_provided(data[self.sender_pos_int[index] + self.language_sender_pos_int : self.sender_pos_int[index] + self.language_sender_pos_int + 2])

    def get_mail_language_from_jp_provided(self, language_data):
        return language_data - self.id_language_char + PokemonNamesForGen.JAPANESE_LANGUAGE

    def get_mail_language_from_jp_mail_data(self, message_data, author_data):
        return self.get_mail_language_from_jp_provided(message_data[0])

    def get_mail_language_from_jp(self, data, index):
        return self.get_mail_language_from_jp_provided(data[self.mail_pos_int[index]])

    def get_mail_language_to_jp(self, mail_language):
        return self.id_language_char + (mail_language - PokemonNamesForGen.JAPANESE_LANGUAGE)

    def prepare_byte_altered_int_mail_data(self, curr_bit_explored, bits_to_save):
        bit_to_preserve = 0
        if curr_bit_explored < len(bits_to_save):
            bit_to_preserve = bits_to_save[curr_bit_explored]
            curr_bit_explored += 1
        return bit_to_preserve, curr_bit_explored

    def get_from_int_conv_table(self, mail_language):
        conversion_table = self.chars_to_jp_en_table
        if mail_language == PokemonNamesForGen.ITALIAN_LANGUAGE:
            conversion_table = self.chars_to_jp_ita_spa_table
        if mail_language == PokemonNamesForGen.SPANISH_LANGUAGE:
            conversion_table = self.chars_to_jp_ita_spa_table
        if mail_language == PokemonNamesForGen.GERMAN_LANGUAGE:
            conversion_table = self.chars_to_jp_ger_fre_table
        if mail_language == PokemonNamesForGen.FRENCH_LANGUAGE:
            conversion_table = self.chars_to_jp_ger_fre_table
        return conversion_table

    def get_to_int_conv_table(self, mail_language):
        conversion_table = self.chars_from_jp_en_table
        if mail_language == PokemonNamesForGen.ITALIAN_LANGUAGE:
            conversion_table = self.chars_from_jp_ita_spa_table
        if mail_language == PokemonNamesForGen.SPANISH_LANGUAGE:
            conversion_table = self.chars_from_jp_ita_spa_table
        if mail_language == PokemonNamesForGen.GERMAN_LANGUAGE:
            conversion_table = self.chars_from_jp_ger_fre_table
        if mail_language == PokemonNamesForGen.FRENCH_LANGUAGE:
            conversion_table = self.chars_from_jp_ger_fre_table
        return conversion_table

    def get_converted_byte(conversion_table, data):
        return conversion_table[data] & 0x7F

    def get_reconverted_byte(reconversion_dict, data):
        try:
            return reconversion_dict[data]
        except:
            print("MISSING IN MAIL JPN RECONVERSION: " + str(data))
        return 0

    def alter_int_mail_data_provided(self, message_data, author_data):
        mail_language = self.get_mail_language_from_int_mail_data(message_data, author_data)
        if mail_language == PokemonNamesForGen.JAPANESE_LANGUAGE:
            return message_data[:], author_data[:]
        if mail_language == PokemonNamesForGen.KOREAN_LANGUAGE:
            # For most bytes, no way to save data...
            # As such, just give up and surrender the last previously
            # converted bytes
            new_message_data = message_data[:]
            new_message_data[0] = self.get_mail_language_to_jp(mail_language)
            return new_message_data, author_data[:]

        conversion_table = self.get_from_int_conv_table(mail_language)

        bytes_to_preserve = [message_data[0], message_data[3], author_data[self.ot_name_real_len_jpn], author_data[self.ot_name_real_len_jpn + 1]]
        bits_to_save = []

        #for i in range(len(bytes_to_preserve)):
        #    print(bytes_to_preserve[i])
        #    print(GSCJPMailConverter.get_converted_byte(conversion_table, bytes_to_preserve[i]))

        for i in range(len(bytes_to_preserve)):
            converted_byte = GSCJPMailConverter.get_converted_byte(conversion_table, bytes_to_preserve[i])
            # Each language has less than 128 letters that can be input...
            # Abuse this with a conversion table
            for j in range(7):
                bits_to_save += [((converted_byte >> j) & 1) << 7]
        #print(bits_to_save)
        curr_bit_explored = 0

        # Put a language-specific byte to identify the base language of the mail...
        new_message_data = [self.get_mail_language_to_jp(mail_language)]
        # Put 2 bytes of the mail as they are
        for i in range(1, 3):
            new_message_data += [message_data[i]]
        # Place an EOL
        new_message_data += [self.utils_class.end_of_line]

        # Now that the EOL has happened, we can place whatever we want without
        # stuff getting corrupted due to control codes...
        # Do 1 bit attached to the letters of the mail converted via
        # the conversion table that converts the letters to 7 bits.
        # 12 bits handled
        for i in range(4, 16):
            bit_to_preserve, curr_bit_explored = self.prepare_byte_altered_int_mail_data(curr_bit_explored, bits_to_save)
            new_message_data += [GSCJPMailConverter.get_converted_byte(conversion_table, message_data[i]) | bit_to_preserve]

        # Pause for newline
        new_message_data += [message_data[16]]

        # 16 bits handled
        # Total: 12 + 16 = 28 bits, the amount of data to preserve.
        for i in range(17, self.jpn_message_len):
            bit_to_preserve, curr_bit_explored = self.prepare_byte_altered_int_mail_data(curr_bit_explored, bits_to_save)
            new_message_data += [GSCJPMailConverter.get_converted_byte(conversion_table, message_data[i]) | bit_to_preserve]

        return new_message_data, author_data

    def alter_int_mail_data(self, data, index):
        mail_language = self.get_mail_language_from_int(data, index)
        if mail_language == PokemonNamesForGen.JAPANESE_LANGUAGE:
            return data

        mail_len = self.base_int_mail_len
        message_data = data[self.mail_pos_int[index] : self.mail_pos_int[index] + mail_len]
        author_data = data[self.sender_pos_int[index] : self.sender_pos_int[index] + self.sender_int_len]

        new_message_data, new_author_data = self.alter_int_mail_data_provided(message_data, author_data)

        for i in range(len(new_message_data)):
            data[self.mail_pos_int[index] + i] = new_message_data[i]

        for i in range(len(new_author_data)):
            data[self.sender_pos_int[index] + i] = new_author_data[i]

        return data

    def preprocess_int_mail(self, data):
        for i in range(6):
            data = self.alter_int_mail_data(data, i)
        return data

    def preprocess_jp_mail(self, data):
        return data

    def alter_jp_mail_data_provided(self, message_data, author_data):
        new_author_data = author_data[:]
        mail_language = self.get_mail_language_from_jp_mail_data(message_data, author_data)
        if (mail_language == PokemonNamesForGen.JAPANESE_LANGUAGE) or (mail_language not in PokemonNamesForGen.sorted_languages_list):
            new_author_data[self.language_sender_pos_int]     = 0x84 # E
            new_author_data[self.language_sender_pos_int + 1] = 0x89 # J
            return message_data[:], new_author_data
        if mail_language == PokemonNamesForGen.KOREAN_LANGUAGE:
            new_message_data = message_data[:]
            new_message_data[0] = self.eol_kor_start_msg_data_replacement
            new_author_data[self.ot_name_real_len_jpn]     = self.end_of_line
            new_author_data[self.ot_name_real_len_jpn + 1] = self.end_of_line
            new_author_data[self.ot_name_real_len_jpn + 2] = self.end_of_line
            new_author_data[self.language_sender_pos_int]     = 0x84 # E
            new_author_data[self.language_sender_pos_int + 1] = 0x8A # K
            return new_message_data, new_author_data

        reconversion_table = self.get_to_int_conv_table(mail_language)

        language_data_to_set = GSCTradingMailData.get_mail_language_data_for_language(mail_language, self.reference_gen)
        for i in range(len(language_data_to_set)):
            new_author_data[self.language_sender_pos_int + i] = language_data_to_set[i]

        # Skip byte 0 for now...
        new_message_data = [0]
        # Put 2 bytes of the mail as they are
        for i in range(1, 3):
            new_message_data += [message_data[i]]
        # Skip byte 3 for now...
        new_message_data += [0]

        bits_preserved = []
        # Now that the EOL has happened, we can place whatever we want without
        # stuff getting corrupted due to control codes...
        # Extract 1 bit attached to the letters of the mail converted via
        # the conversion table that converts the letters to 7 bits.
        # 12 bits handled
        for i in range(4, 16):
            bits_preserved += [(message_data[i] >> 7) & 1]
            real_data_in_table = message_data[i] & 0x7F
            new_message_data += [GSCJPMailConverter.get_reconverted_byte(reconversion_table, real_data_in_table)]

        # Pause for newline
        new_message_data += [message_data[16]]

        # 16 bits handled
        # Total: 12 + 16 = 28 bits, the amount of data preserved.
        for i in range(17, self.jpn_message_len):
            bits_preserved += [(message_data[i] >> 7) & 1]
            real_data_in_table = message_data[i] & 0x7F
            new_message_data += [GSCJPMailConverter.get_reconverted_byte(reconversion_table, real_data_in_table)]

        bytes_preserved_converted = []
        for i in range(len(bits_preserved)):
            if (i % 7) == 0:
                bytes_preserved_converted += [0]
            bytes_preserved_converted[i // 7] |= (bits_preserved[i] << (i % 7))
        #for i in range(len(bytes_preserved_converted)):
        #    print(bytes_preserved_converted[i])
        #    print(GSCJPMailConverter.get_reconverted_byte(reconversion_table, bytes_preserved_converted[i]))

        new_message_data[0] = GSCJPMailConverter.get_reconverted_byte(reconversion_table, bytes_preserved_converted[0])
        new_message_data[3] = GSCJPMailConverter.get_reconverted_byte(reconversion_table, bytes_preserved_converted[1])
        new_author_data[self.ot_name_real_len_jpn] = GSCJPMailConverter.get_reconverted_byte(reconversion_table, bytes_preserved_converted[2])
        new_author_data[self.ot_name_real_len_jpn + 1] = GSCJPMailConverter.get_reconverted_byte(reconversion_table, bytes_preserved_converted[3])

        return new_message_data, new_author_data

    def alter_jp_mail_data(self, data, index):
        mail_language = self.get_mail_language_from_jp(data, index)
        if (mail_language == PokemonNamesForGen.JAPANESE_LANGUAGE) or (mail_language not in PokemonNamesForGen.sorted_languages_list):
            data[self.sender_pos_int[index] + self.language_sender_pos_int]     = 0x84 # E
            data[self.sender_pos_int[index] + self.language_sender_pos_int + 1] = 0x89 # J
            return data

        mail_len = self.base_int_mail_len
        message_data = data[self.mail_pos_int[index] : self.mail_pos_int[index] + mail_len]
        author_data = data[self.sender_pos_int[index] : self.sender_pos_int[index] + self.sender_int_len]

        new_message_data, new_author_data = self.alter_jp_mail_data_provided(message_data, author_data)

        for i in range(len(new_message_data)):
            data[self.mail_pos_int[index] + i] = new_message_data[i]

        for i in range(len(new_author_data)):
            data[self.sender_pos_int[index] + i] = new_author_data[i]

        return data

    def postprocess_int_mail(self, data):
        for i in range(6):
            data = self.alter_jp_mail_data(data, i)
        return data

    def postprocess_jp_mail(self, data):
        return data

    def convert_to_jp(self, data):
        data = self.preprocess_int_mail(data)
        self.mail_converter_pos = self.mail_pos_int
        self.sender_converter_pos = self.sender_pos_int
        self.extra_distance = self.extra_distance_int
        out_data = self.convert(data, self.mail_conversion_table_jp)
        return self.postprocess_jp_mail(out_data)
        
    def convert_to_int(self, data):
        data = self.preprocess_jp_mail(data)
        self.mail_converter_pos = self.mail_pos_jp
        self.sender_converter_pos = self.sender_pos_jp
        self.extra_distance = self.extra_distance_jp
        out_data = self.convert(data, self.mail_conversion_table_int)
        return self.postprocess_int_mail(out_data)
        
    def convert(self, to_convert, converter):
        self.mail_conv_pos = -1
        self.sender_conv_pos = -1
        ret = [0] * len(converter)
        for i in range(len(converter)):
            ret[i] = converter[i](to_convert)
        return ret
    
    def do_zero(self, data):
        return 0
        
    def mail_conversion(self, data):
        self.single_mail_pos += 1
        return data[self.mail_converter_pos[self.mail_conv_pos] + self.single_mail_pos]
        
    def sender_conversion(self, data):
        self.single_sender_pos += 1
        return data[self.sender_converter_pos[self.sender_conv_pos] + self.single_sender_pos]
        
    def extra_conversion(self, data):
        self.extra_conversion_pos += 1
        return data[self.sender_converter_pos[self.sender_conv_pos] + self.extra_distance + self.extra_conversion_pos]
    
    def start_mail_conversion(self, data):
        self.mail_conv_pos += 1
        self.single_mail_pos = 0
        return data[self.mail_converter_pos[self.mail_conv_pos] + self.single_mail_pos]
    
    def start_sender_conversion(self, data):
        self.sender_conv_pos += 1
        self.single_sender_pos = 0
        self.extra_conversion_pos = -1
        return data[self.sender_converter_pos[self.sender_conv_pos] + self.single_sender_pos]
    
    def do_ff(self, data):
        return 0xFF
    
    def do_eol(self, data):
        return self.end_of_line
    
    def do_20(self, data):
        return 0x20

class GSCTradingJP(GSCTrading):
    """
    Class which handles the trading process for the player.
    """
    next_section = 0xFD
    mail_next_section = 0x20
    no_input = 0xFE
    end_of_line = 0x50
    single_text_len = 0xB
    mail_sender_len = 0xE
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
        end_of_gsc_data_pos + (single_text_len * 11): [pokemon_name_len_diff, end_of_line],
        # Add the ones due to Korean special character handling
        end_of_player_name_pos + 2: [player_name_len_diff - 2, end_of_line],
        end_of_gsc_data_pos + 2 + (single_text_len * 0): [player_name_len_diff - 2, end_of_line],
        end_of_gsc_data_pos + 2 + (single_text_len * 1): [player_name_len_diff - 2, end_of_line],
        end_of_gsc_data_pos + 2 + (single_text_len * 2): [player_name_len_diff - 2, end_of_line],
        end_of_gsc_data_pos + 2 + (single_text_len * 3): [player_name_len_diff - 2, end_of_line],
        end_of_gsc_data_pos + 2 + (single_text_len * 4): [player_name_len_diff - 2, end_of_line],
        end_of_gsc_data_pos + 2 + (single_text_len * 5): [player_name_len_diff - 2, end_of_line],
        end_of_gsc_data_pos + 2 + (single_text_len * 6): [pokemon_name_len_diff - 2, end_of_line],
        end_of_gsc_data_pos + 2 + (single_text_len * 7): [pokemon_name_len_diff - 2, end_of_line],
        end_of_gsc_data_pos + 2 + (single_text_len * 8): [pokemon_name_len_diff - 2, end_of_line],
        end_of_gsc_data_pos + 2 + (single_text_len * 9): [pokemon_name_len_diff - 2, end_of_line],
        end_of_gsc_data_pos + 2 + (single_text_len * 10): [pokemon_name_len_diff - 2, end_of_line],
        end_of_gsc_data_pos + 2 + (single_text_len * 11): [pokemon_name_len_diff - 2, end_of_line],
    }, {}, {}, {}]
    special_sections_starter = [next_section, next_section, next_section, mail_next_section, mail_next_section]
    special_sections_sync = [True, True, True, False, False]
    drop_bytes_checks = [[0xA, 0x1B9, 0xC5, 0x241, 0x11D], [next_section, next_section, mail_next_section, no_input, no_input], [0,4,0,0,0]]
    
    def __init__(self, sending_func, receiving_func, connection, menu, kill_function, pre_sleep):
        super(GSCTradingJP, self).__init__(sending_func, receiving_func, connection, menu, kill_function, pre_sleep)
        self.jp_mail_converter = GSCJPMailConverter(self.checks)

    def get_mail_section_id(self):
        return 4

    def get_section_length(self, index, buffered):
        if index != self.get_mail_section_id():
            return self.special_sections_len[index]
        return len(self.jp_mail_converter.mail_checker)

    def get_checker(self, index, buffered):
        if index != self.get_mail_section_id():
            if self.is_gen2_new_mail or buffered:
                return self.checks.checks_map[index]
            return self.checks.checks_map_old[index]
        return self.jp_mail_converter.mail_checker

    def update_mail_data_based_on_language_and_version(self, buffered):
        pass

    def convert_mail_data(self, data, to_device):
        """
        Handles converting the mail data.
        """
        if data is None:
            return None

        if to_device:
            self.utils_class.apply_patches(data, data, self.utils_class, is_mail=True)
            data = self.jp_mail_converter.convert_to_jp(data)
            self.utils_class.create_patches_data(data, data, self.utils_class, is_mail=True, is_japanese=True)
        else:
            self.utils_class.apply_patches(data, data, self.utils_class, is_mail=True, is_japanese=True)
            data = self.jp_mail_converter.convert_to_int(data)
            self.utils_class.create_patches_data(data, data, self.utils_class, is_mail=True)
        return data
