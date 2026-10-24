from .gsc_trading import GSCTrading
from .gsc_trading_data_utils import GSCUtilsLoaders, GSCUtilsMisc, GSCTradingMailData, GSCUtils
from .text_conversions import PokemonNamesForGen

class GSCKORMailConverter:
    """
    Class which handles converting between the GSC Korean mail data
    and the international (extended) format.
    """
    base_folder = "useful_data/gsc/"

    end_of_line = 0x50
    newline = 0x4E
    newline_kor = 0x59
    prohibited_char = 0xFE
    prohibited_char_replacement = 0x2D
    eol_kor_start_msg_data_replacement = 0x2C

    reference_gen = 2
    id_language_char = 0x63
    ot_name_real_len_jpn = 5
    ot_name_real_len_int = 7
    ot_name_real_len_kor = 10 # 5 Korean characters
    language_sender_pos_int = 0x8
    mail_item_mon_ot_info_sender_pos_int = 0xA
    base_kor_mail_newline_pos = 0x20
    base_int_mail_newline_pos = 0x10
    full_converted_kor_mail_len = 63 # Compared to the regular 85 bytes
    pos_last_first_bytes_kor_conv_int = -2
    pos_half_in_corr_byte_kor_conv_int = 34
    base_int_mail_len = 0x21
    base_kor_mail_len = 0x41
    kor_int_mail_non_truncated_language_marker = [0x68, 0x83, 0x73, 0xA0]
    int_kor_mail_language_marker = [0x88, 0x8D, 0x93, 0x00]
    int_kor_mail_corr_bits_len = (base_int_mail_len + ot_name_real_len_int + 6) // 7
    int_kor_mail_language_dup_pos = 0x22
    int_kor_mail_corr_bits_pos = 0x24
    int_kor_mail_language_marker_pos = int_kor_mail_corr_bits_pos + int_kor_mail_corr_bits_len
    int_kor_mail_checksum_pos = base_kor_mail_len - 2 # Do 6 bits per byte, so 12 total bits
    num_valid_user_input_tables = 0xB
    mail_len = 0x41 # 0x21
    sender_int_len = 0xE
    mail_pos_int = [
        (0*mail_len),
        (1*mail_len),
        (2*mail_len),
        (3*mail_len),
        (4*mail_len),
        (5*mail_len)
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

    def get_utils_class(self):
        return GSCUtils

    def get_path(self, target):
        return self.base_folder + target

    def get_mail_language_from_int_provided(self, language_data):
        return GSCTradingMailData.get_int_mail_data_language(language_data, self.reference_gen)

    def get_mail_language_from_int_mail_data(self, message_data, author_data):
        return self.get_mail_language_from_int_provided(author_data[self.language_sender_pos_int : self.language_sender_pos_int + 2])

    def get_mail_language_from_int(self, data, index):
        return self.get_mail_language_from_int_provided(data[self.sender_pos_int[index] + self.language_sender_pos_int : self.sender_pos_int[index] + self.language_sender_pos_int + 2])

    def get_checksum_of_data(checksummable_data):
        checksum = 0
        for i in range(len(checksummable_data)):
            checksum += checksummable_data[i] << (8 * (i % 2))
        return checksum

    def get_mail_language_kor_checksum(self, message_data, author_data):
        return GSCKORMailConverter.get_checksum_of_data(author_data[:self.mail_item_mon_ot_info_sender_pos_int] + message_data[:self.int_kor_mail_checksum_pos])
        checksum = 0
        for i in range(len(checksummable_data)):
            checksum += checksummable_data[i] << (8 * (i % 2))
        return checksum

    def get_mail_language_from_kor_mail_data(self, message_data, author_data):
        # Determine if this is actually an international mail, or just a
        # regular Korean mail
        if message_data[self.base_int_mail_len] != self.end_of_line:
            return PokemonNamesForGen.KOREAN_LANGUAGE
        if author_data[self.ot_name_real_len_int] != self.end_of_line:
            return PokemonNamesForGen.KOREAN_LANGUAGE
        if (message_data[self.int_kor_mail_language_dup_pos] != author_data[self.language_sender_pos_int]) or (message_data[self.int_kor_mail_language_dup_pos + 1] != author_data[self.language_sender_pos_int + 1]):
            return PokemonNamesForGen.KOREAN_LANGUAGE
        for i in range(len(self.int_kor_mail_language_marker)):
            if message_data[self.int_kor_mail_language_marker_pos + i] != self.int_kor_mail_language_marker[i]:
                return PokemonNamesForGen.KOREAN_LANGUAGE
        checksum = self.get_mail_language_kor_checksum(message_data, author_data)
        checksum_byte_1 = message_data[self.int_kor_mail_checksum_pos] & 0x7F
        checksum_byte_2 = message_data[self.int_kor_mail_checksum_pos + 1] & 0x7F
        if message_data[self.int_kor_mail_checksum_pos] == self.prohibited_char_replacement:
            checksum_byte_1 = (self.prohibited_char & 0x7F)
        if message_data[self.int_kor_mail_checksum_pos + 1] == self.prohibited_char_replacement:
            checksum_byte_2 = (self.prohibited_char & 0x7F)
        read_checksum = checksum_byte_1 | (checksum_byte_2 << 7)
        if (checksum & 0x3FFF) != read_checksum:
            return PokemonNamesForGen.KOREAN_LANGUAGE
        # This is an international mail, read the actual language data regularly
        return self.get_mail_language_from_int_mail_data(message_data, author_data)

    def get_mail_language_from_kor(self, data, index):
        return self.get_mail_language_from_kor_mail_data(data[self.mail_pos_int[index] : self.mail_pos_int[index] + self.mail_len], data[self.sender_pos_int[index] : self.sender_pos_int[index] + self.sender_int_len])

    def alter_int_mail_data_provided_not_kor(self, message_data, author_data):
        new_author_data = author_data[:]
        new_message_data = message_data[:]
        while len(new_message_data) < self.base_kor_mail_len:
            new_message_data += [self.end_of_line]

        new_message_data[self.base_int_mail_len] = self.end_of_line
        new_author_data[self.ot_name_real_len_int] = self.end_of_line

        # Store language data
        new_message_data[self.int_kor_mail_language_dup_pos] = author_data[self.language_sender_pos_int]
        new_message_data[self.int_kor_mail_language_dup_pos + 1] = author_data[self.language_sender_pos_int + 1]
        # Store marker to confirm it is an international mail
        for i in range(len(self.int_kor_mail_language_marker)):
            new_message_data[self.int_kor_mail_language_marker_pos + i] = self.int_kor_mail_language_marker[i]

        # Prevent bad bytes from getting to Korean
        corr_bits = []
        for i in range(self.ot_name_real_len_int):
            to_add = 0
            if new_author_data[i] == self.end_of_line:
                pass
            elif new_author_data[i] < 0x70:
                to_add = 1
                new_author_data[i] |= 0x80
            corr_bits += [to_add]
        for i in range(self.base_int_mail_len):
            to_add = 0
            if new_message_data[i] == self.end_of_line:
                pass
            elif (new_message_data[i] == self.newline) or (new_message_data[i] == self.newline_kor):
                new_message_data[i] = self.newline_kor
            elif new_message_data[i] < 0x70:
                to_add = 1
                new_message_data[i] |= 0x80
            corr_bits += [to_add]

        corr_bytes = []
        for i in range(len(corr_bits)):
            if i % 7 == 0:
                corr_bytes += [0x80]
            corr_bytes[i // 7] |= corr_bits[i] << (i % 7)

        # Add the data to the mail
        for i in range(len(corr_bytes)):
            to_add = corr_bytes[i]
            if to_add == self.prohibited_char:
                to_add = self.prohibited_char_replacement
            new_message_data[self.int_kor_mail_corr_bits_pos + i] = to_add

        # Add a checksum
        checksum = self.get_mail_language_kor_checksum(new_message_data, new_author_data)
        checksum_byte_1 = (checksum & 0x7F) | 0x80
        checksum_byte_2 = ((checksum >> 7) & 0x7F) | 0x80
        if checksum_byte_1 == self.prohibited_char:
            checksum_byte_1 = self.prohibited_char_replacement
        if checksum_byte_2 == self.prohibited_char:
            checksum_byte_2 = self.prohibited_char_replacement
        new_message_data[self.int_kor_mail_checksum_pos] = checksum_byte_1
        new_message_data[self.int_kor_mail_checksum_pos + 1] = checksum_byte_2

        return new_message_data, new_author_data

    def determine_has_been_truncated_and_process_data(self, new_total_message_data, post_int_mail_data_bytes, message_data, end_of_post_int_mail_data):
        has_been_truncated = post_int_mail_data_bytes[0] == self.utils_class.end_of_line
        if has_been_truncated:
            return has_been_truncated

        # Place back invalid character(s)
        for i in range(len(post_int_mail_data_bytes)):
            if post_int_mail_data_bytes[i] == self.prohibited_char_replacement:
                post_int_mail_data_bytes[i] = self.prohibited_char
        metadata_non_truncated_bytes = message_data[end_of_post_int_mail_data:end_of_post_int_mail_data + len(self.kor_int_mail_non_truncated_language_marker) + 2]
        for i in range(len(metadata_non_truncated_bytes)):
            if metadata_non_truncated_bytes[i] == self.prohibited_char_replacement:
                metadata_non_truncated_bytes[i] = self.prohibited_char

        # Are the language marked bytes still there?
        if metadata_non_truncated_bytes[:len(self.kor_int_mail_non_truncated_language_marker)] != self.kor_int_mail_non_truncated_language_marker:
            return True

        # Is the checksum okay?
        checksum = GSCKORMailConverter.get_checksum_of_data(new_total_message_data + post_int_mail_data_bytes + metadata_non_truncated_bytes[:-2])
        checksum_byte_1 = (checksum & 0x7F) | 0x80
        checksum_byte_2 = ((checksum >> 7) & 0x7F) | 0x80
        if checksum_byte_1 != metadata_non_truncated_bytes[len(self.kor_int_mail_non_truncated_language_marker)]:
            return True
        if checksum_byte_2 != metadata_non_truncated_bytes[len(self.kor_int_mail_non_truncated_language_marker) + 1]:
            return True

        return False

    def get_reconverted_byte_first_second(self, has_encountered_eol, in_first_bytes, in_second_bytes, i):
        is_eol = False
        to_add_second_byte = 0x0E
        if i < len(in_second_bytes):
            to_add_second_byte = in_second_bytes[i]
            if in_second_bytes[i] == self.end_of_line:
                is_eol = True
                has_encountered_eol = True
        elif has_encountered_eol:
            to_add_second_byte = self.end_of_line
            is_eol = True
        to_add_first_byte = in_first_bytes[i] + 1
        if is_eol:
            to_add_first_byte = self.end_of_line
        return to_add_first_byte, to_add_second_byte, has_encountered_eol

    def alter_int_mail_data_provided_kor(self, message_data, author_data):
        new_author_data = author_data[:]

        # Extract back the data from the mail...
        new_total_message_data = []
        for i in range(self.ot_name_real_len_jpn):
            new_total_message_data += [author_data[i]]

        skipped_newline = False
        for i in range(self.base_int_mail_len - 1):
            to_add = message_data[i + 1]
            if (not skipped_newline) and ((to_add == self.newline) or (to_add == self.newline_kor)):
                skipped_newline = True
                continue
            new_total_message_data += [to_add]

        to_add = message_data[0]
        if to_add == self.eol_kor_start_msg_data_replacement:
            to_add = self.end_of_line
        new_total_message_data += [to_add]
        new_total_message_data += [author_data[self.ot_name_real_len_jpn]]
        new_total_message_data += [author_data[self.ot_name_real_len_jpn + 1]]

        # Place back invalid character(s)
        for i in range(len(new_total_message_data)):
            if new_total_message_data[i] == self.prohibited_char_replacement:
                new_total_message_data[i] = self.prohibited_char

        # Check if mail data has been truncated by games with other languages
        end_of_post_int_mail_data = self.base_int_mail_len + (self.full_converted_kor_mail_len - len(new_total_message_data))
        post_int_mail_data_bytes = message_data[self.base_int_mail_len:end_of_post_int_mail_data]
        assert((len(post_int_mail_data_bytes) + len(new_total_message_data)) == self.full_converted_kor_mail_len)
        has_been_truncated = self.determine_has_been_truncated_and_process_data(new_total_message_data, post_int_mail_data_bytes, message_data, end_of_post_int_mail_data)

        # Preprocess to get one more full characters in...
        # Do it while keeping the order, to improve compatibility with Japanese
        # Little bonus: when sending to Japanese, this makes it so there
        # is a clean cut, and no half-cut characters
        corr_byte_sp = new_total_message_data[self.pos_half_in_corr_byte_kor_conv_int] & 0x7
        if not has_been_truncated:
            corr_byte_sp |= (post_int_mail_data_bytes[0] & 0xF) << 3
        first_byte_sp_1 = (new_total_message_data[self.pos_half_in_corr_byte_kor_conv_int] >> 3) & 0xF
        first_byte_sp_2 = (new_total_message_data[self.pos_half_in_corr_byte_kor_conv_int + 2] & 0x7F) % self.num_valid_user_input_tables
        first_byte_sp_3 = (new_total_message_data[self.pos_half_in_corr_byte_kor_conv_int + 2] & 0x7F) // self.num_valid_user_input_tables
        first_byte_sp_4 = 0
        second_byte_sp_1 = new_total_message_data[self.pos_half_in_corr_byte_kor_conv_int + 1]
        second_byte_sp_2 = new_total_message_data[self.pos_half_in_corr_byte_kor_conv_int + 3]
        second_byte_sp_3 = new_total_message_data[self.pos_half_in_corr_byte_kor_conv_int + 4]
        new_total_message_data[self.pos_half_in_corr_byte_kor_conv_int] = corr_byte_sp | 0x80
        new_total_message_data[self.pos_half_in_corr_byte_kor_conv_int + 1] = (first_byte_sp_1 + (self.num_valid_user_input_tables * first_byte_sp_2)) | 0x80
        new_total_message_data[self.pos_half_in_corr_byte_kor_conv_int + 2] = second_byte_sp_1
        new_total_message_data[self.pos_half_in_corr_byte_kor_conv_int + 3] = second_byte_sp_2
        new_total_message_data[self.pos_half_in_corr_byte_kor_conv_int + 4] = (first_byte_sp_3 + (self.num_valid_user_input_tables * first_byte_sp_4)) | 0x80
        # Add in more data, and complete set by specifying EOL
        new_total_message_data += [second_byte_sp_3]
        if has_been_truncated:
            new_total_message_data += [self.end_of_line]
        else:
            new_total_message_data += post_int_mail_data_bytes[1:]
            assert(len(new_total_message_data) == self.full_converted_kor_mail_len)
            # Restore this missing part from first byte
            first_byte_sp_4 = (new_total_message_data[self.pos_last_first_bytes_kor_conv_int] & 0x7F) // self.num_valid_user_input_tables
            new_total_message_data[self.pos_half_in_corr_byte_kor_conv_int + 4] = (first_byte_sp_3 + (self.num_valid_user_input_tables * first_byte_sp_4)) | 0x80

        #print(new_total_message_data)
        # Reconvert the extracted data to the three arrays
        newline_pos = new_total_message_data[0] & 0x3F
        in_first_bytes = []
        in_second_bytes = []
        in_corr_bytes = []
        has_processed_corr_bytes = False
        i = 1
        while i < len(new_total_message_data):
            if (not has_processed_corr_bytes) and (((len(in_second_bytes) % 7) == 0) or (((len(in_second_bytes) + 1) % 7) == 0)):
                has_processed_corr_bytes = True
                in_corr_bytes += [new_total_message_data[i] & 0x7F]
                i += 1
                continue
            has_processed_corr_bytes = False
            first_byte_merged = new_total_message_data[i] & 0x7F
            in_first_bytes += [first_byte_merged % self.num_valid_user_input_tables]
            in_first_bytes += [first_byte_merged // self.num_valid_user_input_tables]
            i += 1
            if i >= len(new_total_message_data):
                break
            to_add = new_total_message_data[i] & 0x7F
            # Report EOL
            if new_total_message_data[i] == self.end_of_line:
                to_add = 0x80
            in_second_bytes += [to_add]
            i += 1
            if i >= len(new_total_message_data):
                break
            to_add = new_total_message_data[i] & 0x7F
            # Report EOL
            if new_total_message_data[i] == self.end_of_line:
                to_add = 0x80
            in_second_bytes += [to_add]
            i += 1

        # The first bytes are odd, meaning the last one is extra...
        # And we use it to restore the 4th sp first byte
        num_base_mail_kor_chars = (self.ot_name_real_len_kor + self.base_kor_mail_len) // 2
        if len(in_first_bytes) >= num_base_mail_kor_chars:
            assert(len(in_first_bytes) == (num_base_mail_kor_chars + 1))
            in_first_bytes = in_first_bytes[:num_base_mail_kor_chars]

        # Get bits out of the stored corr bytes
        in_corr_bits = []
        for i in range(len(in_corr_bytes)):
            for j in range(7):
                to_add = 0
                if (in_corr_bytes[i] & (1 << j)) != 0:
                    to_add = 0x80
                in_corr_bits += [to_add]

        #print(in_corr_bytes)
        #print(len(in_corr_bits))
        # Restore the second bytes to their regular state
        for i in range(len(in_second_bytes)):
            # Restore EOL
            if in_second_bytes[i] == 0x80:
                in_second_bytes[i] = self.end_of_line
            else:
                in_second_bytes[i] |= in_corr_bits[i]

        # Copy OT data back
        has_encountered_eol = False
        for i in range(self.ot_name_real_len_kor // 2):
            to_add_first_byte, to_add_second_byte, has_encountered_eol = self.get_reconverted_byte_first_second(has_encountered_eol, in_first_bytes, in_second_bytes, i)
            new_author_data[i * 2] = to_add_first_byte
            new_author_data[(i * 2) + 1] = to_add_second_byte

        new_message_data = [self.end_of_line] * self.mail_len
        # Copy message data back
        out_pos = 0
        has_encountered_eol = False
        for i in range(self.ot_name_real_len_kor // 2, len(in_first_bytes)):
            if out_pos == newline_pos:
                new_message_data[out_pos] = self.newline_kor
                out_pos += 1
            to_add_first_byte, to_add_second_byte, has_encountered_eol = self.get_reconverted_byte_first_second(has_encountered_eol, in_first_bytes, in_second_bytes, i)
            new_message_data[out_pos] = to_add_first_byte
            out_pos += 1
            new_message_data[out_pos] = to_add_second_byte
            out_pos += 1

        for i in range(out_pos, self.mail_len):
            if i == newline_pos:
                new_message_data[i] = self.newline_kor

        return new_message_data, new_author_data

    def alter_int_mail_data_provided(self, message_data, author_data):
        mail_language = self.get_mail_language_from_int_mail_data(message_data, author_data)

        if mail_language != PokemonNamesForGen.KOREAN_LANGUAGE:
            # Change back bad characters, if they exist...
            return self.alter_int_mail_data_provided_not_kor(message_data, author_data)
        return self.alter_int_mail_data_provided_kor(message_data, author_data)

    def alter_int_mail_data(self, data, index):

        mail_len = self.base_kor_mail_len
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

    def preprocess_kor_mail(self, data):
        return data

    def split_info_of_kor_char_data(self, data, length_to_do, ack_newline):
        out_first_bytes = []
        out_second_bytes = []
        out_corr_bits = []

        newline_pos = -1
        i = 0
        while i < length_to_do:
            is_eol = data[i] == self.end_of_line
            is_newline = ack_newline and ((data[i] == self.newline) or (data[i] == self.newline_kor))
            if is_newline:
                newline_pos = i
                i += 1
                ack_newline = False
                continue
            # Do not do half-bytes, clearly an error condition
            if (i + 1) >= length_to_do:
                break
            first_byte = (data[i] & 0xF) - 1
            if (first_byte < 0) or (first_byte >= self.num_valid_user_input_tables):
                first_byte = self.num_valid_user_input_tables - 1
            second_byte = (data[i + 1] & 0x7F) + 0x80
            corr_bit = 0
            if (data[i + 1] & 0x80) != 0:
                corr_bit = 1
            if is_eol:
                second_byte = self.end_of_line
                corr_bit = 0
            out_first_bytes += [first_byte]
            out_second_bytes += [second_byte]
            out_corr_bits += [corr_bit]
            i += 2
        return out_first_bytes, out_second_bytes, out_corr_bits, newline_pos

    def alter_kor_mail_data_provided_kor(self, message_data, author_data):
        new_author_data = author_data[:]

        # Split information for each Korean character into the 12.5 bits
        # (For information, read the mail conversion notes)
        ofb_ot, osb_ot, ocb_ot, nl_ot = self.split_info_of_kor_char_data(author_data, self.ot_name_real_len_kor, False)
        ofb_msg, osb_msg, ocb_msg, nl_msg = self.split_info_of_kor_char_data(message_data, self.base_kor_mail_len, True)

        # Priority to trainer data (*_ot), then message (*_msg)
        out_first_bytes = ofb_ot + ofb_msg
        out_second_bytes = osb_ot + osb_msg
        bits_preserved = ocb_ot + ocb_msg

        bytes_preserved = []
        for i in range(len(bits_preserved)):
            if (i % 7) == 0:
                bytes_preserved += [0x80]
            bytes_preserved[i // 7] |= (bits_preserved[i] << (i % 7))

        # Must be within the first 16 korean mail characters, so it's always encountered
        if (nl_msg < 0) or (nl_msg > self.base_kor_mail_newline_pos):
            nl_msg = self.base_kor_mail_newline_pos
        # There is one extra bit available here...
        # Keep it for protocol, for future revisions, maybe...?
        new_total_message_data = [nl_msg | 0x80]

        # Add the data to an array that will be later inserted into the available characters.
        # Loop incremented by 2 each iteration, as 2 Korean characters are processed
        # every iteration
        for i in range(0, len(out_second_bytes), 2):
            # Do this (instead of a simple (i % 7) == 0) since 7 isn't a multiple of 2
            if ((i % 7) == 0) or (((i + 1) % 7) == 0):
                new_total_message_data += [bytes_preserved[(i + 6) // 7]]

            out_first_byte_1 = out_first_bytes[i]
            out_first_byte_2 = 0
            if (i + 1) < len(out_second_bytes):
                out_first_byte_2 = out_first_bytes[i + 1]

            new_total_message_data += [(out_first_byte_1 + (self.num_valid_user_input_tables * out_first_byte_2)) | 0x80]

            new_total_message_data += [out_second_bytes[i]]

            if (i + 1) < len(out_second_bytes):
                new_total_message_data += [out_second_bytes[i + 1]]

        #print(new_total_message_data)
        # Postprocess to get one more full characters in...
        # Do it while keeping the order, to improve compatibility with Japanese
        # Little bonus: when sending to Japanese, this makes it so there
        # is a clean cut, and no half-cut characters
        corr_byte_sp = new_total_message_data[self.pos_half_in_corr_byte_kor_conv_int] & 0x7F
        first_byte_sp_1 = (new_total_message_data[self.pos_half_in_corr_byte_kor_conv_int + 1] & 0x7F) % self.num_valid_user_input_tables
        first_byte_sp_2 = (new_total_message_data[self.pos_half_in_corr_byte_kor_conv_int + 1] & 0x7F) // self.num_valid_user_input_tables
        first_byte_sp_3 = (new_total_message_data[self.pos_half_in_corr_byte_kor_conv_int + 4] & 0x7F) % self.num_valid_user_input_tables
        first_byte_sp_4 = (new_total_message_data[self.pos_half_in_corr_byte_kor_conv_int + 4] & 0x7F) // self.num_valid_user_input_tables
        second_byte_sp_1 = new_total_message_data[self.pos_half_in_corr_byte_kor_conv_int + 2]
        second_byte_sp_2 = new_total_message_data[self.pos_half_in_corr_byte_kor_conv_int + 3]
        second_byte_sp_3 = new_total_message_data[self.pos_half_in_corr_byte_kor_conv_int + 5]
        new_total_message_data[self.pos_half_in_corr_byte_kor_conv_int] = ((corr_byte_sp & 0x07) | (first_byte_sp_1 << 3)) | 0x80
        new_total_message_data[self.pos_half_in_corr_byte_kor_conv_int + 1] = second_byte_sp_1
        new_total_message_data[self.pos_half_in_corr_byte_kor_conv_int + 2] = (first_byte_sp_2 + (self.num_valid_user_input_tables * first_byte_sp_3)) | 0x80
        new_total_message_data[self.pos_half_in_corr_byte_kor_conv_int + 3] = second_byte_sp_2
        new_total_message_data[self.pos_half_in_corr_byte_kor_conv_int + 4] = second_byte_sp_3
        new_total_message_data[self.pos_half_in_corr_byte_kor_conv_int + 5] = (corr_byte_sp >> 3) | 0x80
        # Save the removed first_byte_sp_4 at the end of the actual mail data
        first_byte_sp_final = (new_total_message_data[self.pos_last_first_bytes_kor_conv_int] & 0x7F) % self.num_valid_user_input_tables
        new_total_message_data[self.pos_last_first_bytes_kor_conv_int] = (first_byte_sp_final + (first_byte_sp_4 * self.num_valid_user_input_tables)) | 0x80

        # Add metadata to determine whether mail data has been truncated or not
        new_total_message_data += self.kor_int_mail_non_truncated_language_marker
        checksum = GSCKORMailConverter.get_checksum_of_data(new_total_message_data)
        checksum_byte_1 = (checksum & 0x7F) | 0x80
        checksum_byte_2 = ((checksum >> 7) & 0x7F) | 0x80
        new_total_message_data += [checksum_byte_1] + [checksum_byte_2]

        # Replace invalid character(s)
        for i in range(len(new_total_message_data)):
            if new_total_message_data[i] == self.prohibited_char:
                new_total_message_data[i] = self.prohibited_char_replacement

        #print(new_total_message_data)
        # Start placing the data into the available space
        new_message_data = [0]
        pos_in_copy = 0
        # Avoid placing data where it could be removed by JPN conversion
        for i in range(self.ot_name_real_len_jpn):
            new_author_data[i] = new_total_message_data[pos_in_copy]
            pos_in_copy += 1

        # Skip first byte and newline, hence -2
        for _ in range(self.base_int_mail_len - 2):
            new_message_data += [new_total_message_data[pos_in_copy]]
            pos_in_copy += 1
            if len(new_message_data) == self.base_int_mail_newline_pos:
                new_message_data += [self.newline]

        new_message_data[0] = new_total_message_data[pos_in_copy]
        if new_message_data[0] == self.end_of_line:
            new_message_data[0] = self.eol_kor_start_msg_data_replacement
        pos_in_copy += 1
        new_author_data[self.ot_name_real_len_jpn] = new_total_message_data[pos_in_copy]
        pos_in_copy += 1
        new_author_data[self.ot_name_real_len_jpn + 1] = new_total_message_data[pos_in_copy]
        pos_in_copy += 1
        new_author_data[self.ot_name_real_len_jpn + 2] = self.end_of_line

        # Data that may or may not be used by other Korean games...
        new_message_data += new_total_message_data[pos_in_copy:]

        # Signal Korean language
        new_author_data[self.language_sender_pos_int]     = 0x84 # E
        new_author_data[self.language_sender_pos_int + 1] = 0x8A # K
        #print(new_total_message_data)
        #print(len(new_total_message_data))
        # Len actual message minus the extra metadata (recognizable pattern + 2-bytes checksum)
        assert((len(new_total_message_data) - len(self.kor_int_mail_non_truncated_language_marker) - 2) == self.full_converted_kor_mail_len)

        return new_message_data, new_author_data

    def alter_kor_mail_data_provided_not_kor(self, message_data, author_data):
        new_author_data = author_data[:]
        new_message_data = message_data[:]

        # Need to set back the special characters...

        # Get the correction bytes back
        corr_bytes = []
        for i in range(self.int_kor_mail_corr_bits_len):
            to_add = message_data[self.int_kor_mail_corr_bits_pos + i]
            if to_add == self.prohibited_char:
                to_add = self.prohibited_char_replacement
            corr_bytes += [to_add]

        # Convert to correction masks
        corr_masks = []
        for i in range(len(corr_bytes)):
            for j in range(7):
                to_add = 0
                if (corr_bytes[i] & (1 << j)) != 0:
                    to_add = 0x80
                corr_masks += [~to_add]

        # Restore the original OT data
        for i in range(self.ot_name_real_len_int):
            new_author_data[i] = author_data[i] & corr_masks[i]

        # Restore the original message data
        for i in range(self.base_int_mail_len):
            new_message_data[i] = message_data[i] & corr_masks[self.ot_name_real_len_int + i]
            if (new_message_data[i] == self.newline) or (new_message_data[i] == self.newline_kor):
                new_message_data[i] = self.newline

        return new_message_data, new_author_data

    def alter_kor_mail_data_provided(self, message_data, author_data):
        mail_language = self.get_mail_language_from_kor_mail_data(message_data, author_data)

        if mail_language != PokemonNamesForGen.KOREAN_LANGUAGE:
            # Change back bad characters, if they exist...
            return self.alter_kor_mail_data_provided_not_kor(message_data, author_data)
        return self.alter_kor_mail_data_provided_kor(message_data, author_data)

    def alter_kor_mail_data(self, data, index):

        mail_len = self.base_kor_mail_len
        message_data = data[self.mail_pos_int[index] : self.mail_pos_int[index] + mail_len]
        author_data = data[self.sender_pos_int[index] : self.sender_pos_int[index] + self.sender_int_len]

        new_message_data, new_author_data = self.alter_kor_mail_data_provided(message_data, author_data)

        for i in range(len(new_message_data)):
            data[self.mail_pos_int[index] + i] = new_message_data[i]

        for i in range(len(new_author_data)):
            data[self.sender_pos_int[index] + i] = new_author_data[i]

        return data

    def postprocess_int_mail(self, data):
        for i in range(6):
            data = self.alter_kor_mail_data(data, i)
        return data

    def postprocess_kor_mail(self, data):
        return data

    def convert_to_kor(self, data):
        data = self.preprocess_int_mail(data)
        return self.postprocess_kor_mail(data)
        
    def convert_to_int(self, data):
        data = self.preprocess_kor_mail(data)
        return self.postprocess_int_mail(data)

class GSCTradingKOR(GSCTrading):
    """
    Class which handles the trading process for the player.
    """
    next_section = 0xFD
    mail_next_section = 0x20
    mail_next_section_kor = 0x52
    no_input = 0xFE
    end_of_line = 0x50
    # Specially handled by the generic code...
    fillers = [{}, {}, {}, {}, {}, {}]
    special_sections_starter = [next_section, next_section, next_section, mail_next_section, mail_next_section, mail_next_section_kor]
    special_sections_sync = [True, True, True, False, False, False]
    drop_bytes_checks = [[0xA, 0x1B9, 0xC5, 0x241, 0x11D, 0x241], [next_section, next_section, mail_next_section, no_input, no_input, no_input], [0,4,0,0,0,0]]
    
    def __init__(self, sending_func, receiving_func, connection, menu, kill_function, pre_sleep):
        super(GSCTradingKOR, self).__init__(sending_func, receiving_func, connection, menu, kill_function, pre_sleep)
        self.kor_mail_converter = GSCKORMailConverter(self.checks)

    def get_mail_section_id(self):
        return 5

    def get_section_length(self, index, buffered):
        if index != self.get_mail_section_id():
            return self.special_sections_len[index]
        return self.special_sections_len[self.base_mail_index]

    def get_checker(self, index, buffered):
        if index != self.get_mail_section_id():
            if self.is_gen2_new_mail or buffered:
                return self.checks.checks_map[index]
            return self.checks.checks_map_old[index]
        if self.is_gen2_new_mail or buffered:
            return self.checks.checks_map[self.base_mail_index]
        return self.checks.checks_map_old[self.base_mail_index]

    def convert_mail_data(self, data, to_device):
        """
        Handles converting the mail data.
        """
        if data is not None:
            if to_device:
                self.utils_class.apply_patches(data, data, self.utils_class, is_mail=True)
                data = self.kor_mail_converter.convert_to_kor(data)
                self.utils_class.create_patches_data(data, data, self.utils_class, is_mail=True)
            else:
                self.utils_class.apply_patches(data, data, self.utils_class, is_mail=True)
                data = self.kor_mail_converter.convert_to_int(data)
                self.utils_class.create_patches_data(data, data, self.utils_class, is_mail=True)
        return data
