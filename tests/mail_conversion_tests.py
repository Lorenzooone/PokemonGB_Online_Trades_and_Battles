import unittest
import sys

class MailConversionTests(unittest.TestCase):

    base_folder = "./tests/"
    en_mail_example_path = "mail_example_en.bin"
    jpn_mail_example_path = "mail_example_jpn.bin"
    kor_mail_example_path = "mail_example_kor.bin"
    kor_mail_example2_path = "mail_example_kor2.bin"

    def test_mail_to_jpn_back_single_chars(self):
        """
        Check that all the characters get converted back and forth properly...
        """
        sys.path.append(sys.path[0] + '/..')

        from utilities.gsc_trading_data_utils import GSCUtils, GSCUtilsMisc, GSCChecks
        from utilities.gsc_trading_jp import GSCJPMailConverter

        en_mail_example = GSCUtilsMisc.read_data(self.get_path(self.en_mail_example_path))
        self.assertFalse(en_mail_example is None)

        checks = GSCChecks([0,0,0], True)
        jp_mail_converter = GSCJPMailConverter(checks)

        message_data = en_mail_example[:jp_mail_converter.mail_len]
        message_data = message_data[:jp_mail_converter.base_int_mail_len]
        author_data = en_mail_example[jp_mail_converter.mail_len:]

        mail_language = jp_mail_converter.get_mail_language_from_int_mail_data(message_data, author_data)
        conversion_table = jp_mail_converter.get_from_int_conv_table(mail_language)
        reconversion_table = jp_mail_converter.get_to_int_conv_table(mail_language)

        for i in range(len(message_data)):
            converted_byte = GSCJPMailConverter.get_converted_byte(conversion_table, message_data[i])
            reconverted_byte = GSCJPMailConverter.get_reconverted_byte(reconversion_table, converted_byte)
            if converted_byte != 0:
                self.assertEqual(message_data[i], reconverted_byte)

        for i in range(jp_mail_converter.ot_name_real_len_int):
            converted_byte = GSCJPMailConverter.get_converted_byte(conversion_table, author_data[i])
            reconverted_byte = GSCJPMailConverter.get_reconverted_byte(reconversion_table, converted_byte)
            if converted_byte != 0:
                self.assertEqual(author_data[i], reconverted_byte)

    def test_mail_to_jpn_and_back(self):
        """
        Check that the actual mail gets converted back and forth properly...
        """
        sys.path.append(sys.path[0] + '/..')

        from utilities.gsc_trading_data_utils import GSCUtils, GSCUtilsMisc, GSCChecks
        from utilities.gsc_trading_jp import GSCJPMailConverter

        en_mail_example = GSCUtilsMisc.read_data(self.get_path(self.en_mail_example_path))
        self.assertFalse(en_mail_example is None)

        checks = GSCChecks([0,0,0], True)
        jp_mail_converter = GSCJPMailConverter(checks)

        # Convert forward
        message_data = en_mail_example[:jp_mail_converter.mail_len]
        message_data = message_data[:jp_mail_converter.base_int_mail_len]
        author_data = en_mail_example[jp_mail_converter.mail_len:]
        new_message_data, new_author_data = jp_mail_converter.alter_int_mail_data_provided(message_data, author_data)

        # Convert backwards
        altered_message_data, altered_author_data = jp_mail_converter.alter_jp_mail_data_provided(new_message_data, new_author_data)

        #print(message_data)
        #print(new_message_data)
        #print(altered_message_data)
        #print(author_data)
        #print(new_author_data)
        #print(altered_author_data)
        self.assertTrue(altered_message_data == message_data)
        self.assertTrue(altered_author_data == author_data)

    def test_mail_from_jpn_and_back(self):
        """
        Check that the actual mail gets converted back and forth properly...
        """
        sys.path.append(sys.path[0] + '/..')

        from utilities.gsc_trading_data_utils import GSCUtils, GSCUtilsMisc, GSCChecks
        from utilities.gsc_trading_jp import GSCJPMailConverter

        jpn_mail_example = GSCUtilsMisc.read_data(self.get_path(self.jpn_mail_example_path))
        self.assertFalse(jpn_mail_example is None)

        checks = GSCChecks([0,0,0], True)
        jp_mail_converter = GSCJPMailConverter(checks)

        # Convert forward
        message_data = jpn_mail_example[:jp_mail_converter.mail_len]
        message_data = message_data[:jp_mail_converter.base_int_mail_len]
        author_data = jpn_mail_example[jp_mail_converter.mail_len:]
        new_message_data, new_author_data = jp_mail_converter.alter_jp_mail_data_provided(message_data, author_data)

        # Convert backwards
        altered_message_data, altered_author_data = jp_mail_converter.alter_int_mail_data_provided(new_message_data, new_author_data)
        # This gets added on during conversion, ignored by jpn mail
        altered_author_data[jp_mail_converter.language_sender_pos_int] = author_data[jp_mail_converter.language_sender_pos_int]
        altered_author_data[jp_mail_converter.language_sender_pos_int + 1] = author_data[jp_mail_converter.language_sender_pos_int + 1]

        self.assertTrue(altered_message_data == message_data)
        self.assertTrue(altered_author_data == author_data)

    def test_mail_to_kor_and_back(self):
        """
        Check that the actual mail gets converted back and forth properly...
        """
        sys.path.append(sys.path[0] + '/..')

        from utilities.gsc_trading_data_utils import GSCUtils, GSCUtilsMisc, GSCChecks
        from utilities.gsc_trading_kor import GSCKORMailConverter

        en_mail_example = GSCUtilsMisc.read_data(self.get_path(self.en_mail_example_path))
        self.assertFalse(en_mail_example is None)

        checks = GSCChecks([0,0,0], True)
        kor_mail_converter = GSCKORMailConverter(checks)

        # Convert forward
        message_data = en_mail_example[:kor_mail_converter.mail_len]
        message_data = message_data[:kor_mail_converter.base_int_mail_len]
        author_data = en_mail_example[kor_mail_converter.mail_len:]
        new_message_data, new_author_data = kor_mail_converter.alter_int_mail_data_provided(message_data, author_data)

        # Convert backwards
        altered_message_data, altered_author_data = kor_mail_converter.alter_kor_mail_data_provided(new_message_data, new_author_data)

        #print(message_data)
        #print(new_message_data)
        #print(altered_message_data)
        #print(author_data)
        #print(new_author_data)
        #print(altered_author_data)

        self.assertTrue(altered_message_data[:kor_mail_converter.base_int_mail_len] == message_data[:kor_mail_converter.base_int_mail_len])
        self.assertTrue(altered_author_data == author_data)

    def test_mail_from_kor_to_kor(self):
        """
        Check that the actual mail gets converted back and forth properly...
        """
        sys.path.append(sys.path[0] + '/..')

        from utilities.gsc_trading_data_utils import GSCUtils, GSCUtilsMisc, GSCChecks
        from utilities.gsc_trading_kor import GSCKORMailConverter

        kor_mail_example = GSCUtilsMisc.read_data(self.get_path(self.kor_mail_example_path))
        kor_mail_example2 = GSCUtilsMisc.read_data(self.get_path(self.kor_mail_example2_path))
        self.assertFalse(kor_mail_example is None)
        self.assertFalse(kor_mail_example2 is None)

        checks = GSCChecks([0,0,0], True)
        kor_mail_converter = GSCKORMailConverter(checks)

        # Convert forward
        message_data = kor_mail_example[:kor_mail_converter.mail_len]
        author_data = kor_mail_example[kor_mail_converter.mail_len:]
        new_message_data, new_author_data = kor_mail_converter.alter_kor_mail_data_provided(message_data, author_data)

        # Convert backwards
        altered_message_data, altered_author_data = kor_mail_converter.alter_int_mail_data_provided(new_message_data, new_author_data)

        self.assertTrue(altered_message_data == message_data)
        self.assertTrue(altered_author_data == author_data)

        # Convert forward
        message_data = kor_mail_example2[:kor_mail_converter.mail_len]
        author_data = kor_mail_example2[kor_mail_converter.mail_len:]
        new_message_data, new_author_data = kor_mail_converter.alter_kor_mail_data_provided(message_data, author_data)

        # Convert backwards
        altered_message_data, altered_author_data = kor_mail_converter.alter_int_mail_data_provided(new_message_data, new_author_data)
        # Handle missing bytes due to size
        
        #print(message_data)
        #print(altered_message_data)
        #print(author_data)
        #print(altered_author_data)

        self.assertTrue(altered_message_data == message_data)
        self.assertTrue(altered_author_data == author_data)

    def test_mail_from_kor_and_back(self):
        """
        Check that the actual mail gets converted back and forth properly...
        """
        sys.path.append(sys.path[0] + '/..')

        from utilities.gsc_trading_data_utils import GSCUtils, GSCUtilsMisc, GSCChecks
        from utilities.gsc_trading_kor import GSCKORMailConverter

        kor_mail_example = GSCUtilsMisc.read_data(self.get_path(self.kor_mail_example_path))
        kor_mail_example2 = GSCUtilsMisc.read_data(self.get_path(self.kor_mail_example2_path))
        self.assertFalse(kor_mail_example is None)
        self.assertFalse(kor_mail_example2 is None)

        checks = GSCChecks([0,0,0], True)
        kor_mail_converter = GSCKORMailConverter(checks)

        # Convert forward
        message_data = kor_mail_example[:kor_mail_converter.mail_len]
        author_data = kor_mail_example[kor_mail_converter.mail_len:]
        new_message_data, new_author_data = kor_mail_converter.alter_kor_mail_data_provided(message_data, author_data)

        # Truncate mail data
        for i in range(len(new_message_data) - kor_mail_converter.base_int_mail_len):
            new_message_data[kor_mail_converter.base_int_mail_len + i] = kor_mail_converter.end_of_line

        # Convert backwards
        altered_message_data, altered_author_data = kor_mail_converter.alter_int_mail_data_provided(new_message_data, new_author_data)
        # Handle missing bytes due to size

        max_message_same_bytes = 37

        self.assertTrue(altered_message_data[:max_message_same_bytes] == message_data[:max_message_same_bytes])
        self.assertTrue(altered_author_data == author_data)

        # Convert forward
        message_data = kor_mail_example2[:kor_mail_converter.mail_len]
        author_data = kor_mail_example2[kor_mail_converter.mail_len:]
        new_message_data, new_author_data = kor_mail_converter.alter_kor_mail_data_provided(message_data, author_data)

        # Truncate mail data
        for i in range(len(new_message_data) - kor_mail_converter.base_int_mail_len):
            new_message_data[kor_mail_converter.base_int_mail_len + i] = kor_mail_converter.end_of_line

        # Convert backwards
        altered_message_data, altered_author_data = kor_mail_converter.alter_int_mail_data_provided(new_message_data, new_author_data)
        # Handle missing bytes due to size
        
        #print(message_data)
        #print(altered_message_data)
        #print(author_data)
        #print(altered_author_data)

        self.assertTrue(altered_message_data[:max_message_same_bytes] == message_data[:max_message_same_bytes])
        self.assertTrue(altered_author_data == author_data)

    def test_mail_from_jpn_to_kor_and_back(self):
        """
        Check that the actual mail gets converted back and forth properly...
        """
        sys.path.append(sys.path[0] + '/..')

        from utilities.gsc_trading_data_utils import GSCUtils, GSCUtilsMisc, GSCChecks
        from utilities.gsc_trading_kor import GSCKORMailConverter
        from utilities.gsc_trading_jp import GSCJPMailConverter

        jpn_mail_example = GSCUtilsMisc.read_data(self.get_path(self.jpn_mail_example_path))
        self.assertFalse(jpn_mail_example is None)

        checks = GSCChecks([0,0,0], True)
        jp_mail_converter = GSCJPMailConverter(checks)
        kor_mail_converter = GSCKORMailConverter(checks)

        # Convert forward to en
        message_data = jpn_mail_example[:jp_mail_converter.mail_len]
        message_data = message_data[:jp_mail_converter.base_int_mail_len]
        author_data = jpn_mail_example[jp_mail_converter.mail_len:]
        new_message_data, new_author_data = jp_mail_converter.alter_jp_mail_data_provided(message_data, author_data)

        # Convert forward to kor
        kor_new_message_data, kor_new_author_data = kor_mail_converter.alter_int_mail_data_provided(new_message_data, new_author_data)

        # Convert backwards to en
        altered_kor_message_data, altered_kor_author_data = kor_mail_converter.alter_kor_mail_data_provided(kor_new_message_data, kor_new_author_data)

        # Convert backwards to jpn
        altered_message_data, altered_author_data = jp_mail_converter.alter_int_mail_data_provided(altered_kor_message_data, altered_kor_author_data)
        # This gets added on during conversion, ignored by jpn mail
        altered_author_data[jp_mail_converter.language_sender_pos_int] = author_data[jp_mail_converter.language_sender_pos_int]
        altered_author_data[jp_mail_converter.language_sender_pos_int + 1] = author_data[jp_mail_converter.language_sender_pos_int + 1]

        #print(message_data)
        #print(new_message_data)
        #print(altered_message_data)
        #print(author_data)
        #print(altered_author_data)
        #print(kor_new_author_data)
        #print(new_author_data)
        #print(altered_kor_author_data)

        self.assertTrue(new_message_data[:kor_mail_converter.base_int_mail_len] == altered_kor_message_data[:kor_mail_converter.base_int_mail_len])
        self.assertTrue(new_author_data == altered_kor_author_data)

        self.assertTrue(altered_message_data[:kor_mail_converter.base_int_mail_len] == message_data[:kor_mail_converter.base_int_mail_len])
        self.assertTrue(altered_author_data == author_data)

    def test_mail_from_kor_to_jpn_and_back(self):
        """
        Check that the actual mail gets converted back and forth properly...
        """
        sys.path.append(sys.path[0] + '/..')

        from utilities.gsc_trading_data_utils import GSCUtils, GSCUtilsMisc, GSCChecks
        from utilities.gsc_trading_kor import GSCKORMailConverter
        from utilities.gsc_trading_jp import GSCJPMailConverter

        kor_mail_example = GSCUtilsMisc.read_data(self.get_path(self.kor_mail_example_path))
        kor_mail_example2 = GSCUtilsMisc.read_data(self.get_path(self.kor_mail_example2_path))
        self.assertFalse(kor_mail_example is None)
        self.assertFalse(kor_mail_example2 is None)

        checks = GSCChecks([0,0,0], True)
        jp_mail_converter = GSCJPMailConverter(checks)
        kor_mail_converter = GSCKORMailConverter(checks)

        # Convert forward to en
        message_data = kor_mail_example[:kor_mail_converter.mail_len]
        author_data = kor_mail_example[kor_mail_converter.mail_len:]
        new_message_data, new_author_data = kor_mail_converter.alter_kor_mail_data_provided(message_data, author_data)

        # Truncate mail data
        for i in range(len(new_message_data) - kor_mail_converter.base_int_mail_len):
            new_message_data[kor_mail_converter.base_int_mail_len + i] = kor_mail_converter.end_of_line

        # Convert forward to jpn
        jpn_message_data, jpn_author_data = jp_mail_converter.alter_int_mail_data_provided(new_message_data, new_author_data)

        # Convert backwards to en
        altered_jpn_message_data, altered_jpn_author_data = jp_mail_converter.alter_jp_mail_data_provided(jpn_message_data, jpn_author_data)

        # Convert backwards to kor
        altered_message_data, altered_author_data = kor_mail_converter.alter_int_mail_data_provided(altered_jpn_message_data, altered_jpn_author_data)

        # Handle missing bytes due to size

        max_message_same_bytes = 33
        
        #print(message_data[:max_message_same_bytes])
        #print(altered_message_data[:max_message_same_bytes])
        #print(author_data)
        #print(altered_author_data)

        self.assertTrue(altered_message_data[:max_message_same_bytes] == message_data[:max_message_same_bytes])
        self.assertTrue(altered_author_data == author_data)

        # Convert forward to en
        message_data = kor_mail_example2[:kor_mail_converter.mail_len]
        author_data = kor_mail_example2[kor_mail_converter.mail_len:]
        new_message_data, new_author_data = kor_mail_converter.alter_kor_mail_data_provided(message_data, author_data)

        # Truncate mail data
        for i in range(len(new_message_data) - kor_mail_converter.base_int_mail_len):
            new_message_data[kor_mail_converter.base_int_mail_len + i] = kor_mail_converter.end_of_line

        # Convert forward to jpn
        jpn_message_data, jpn_author_data = jp_mail_converter.alter_int_mail_data_provided(new_message_data, new_author_data)

        # Convert backwards to en
        altered_jpn_message_data, altered_jpn_author_data = jp_mail_converter.alter_jp_mail_data_provided(jpn_message_data, jpn_author_data)

        # Convert backwards to kor
        altered_message_data, altered_author_data = kor_mail_converter.alter_int_mail_data_provided(altered_jpn_message_data, altered_jpn_author_data)

        # Handle missing bytes due to size
        
        #print(message_data[:max_message_same_bytes])
        #print(altered_message_data[:max_message_same_bytes])
        #print(author_data)
        #print(altered_author_data)

        self.assertTrue(altered_message_data[:max_message_same_bytes] == message_data[:max_message_same_bytes])
        self.assertTrue(altered_author_data == author_data)

    def get_path(self, target):
        return self.base_folder + target

if __name__ == "__main__":
    unittest.main()
