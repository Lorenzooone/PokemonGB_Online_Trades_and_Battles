import unittest
import sys

class PokemonNamesConversionTests(unittest.TestCase):

    base_folder = "./tests/"
    en_mon_example_path = "mon_example_en_g2.bin"
    jpn_mon_example_path = "mon_example_jpn_g2.bin"
    kor_mon_example_path = "mon_example_kor_g2.bin"
    en_old_mon_example_path = "mon_example_en_g2_old.bin"

    def test_mon_kor_to_int_back(self):
        """
        Check that all the characters get converted back and forth properly...
        """
        sys.path.append(sys.path[0] + '/..')

        from utilities.gsc_trading_data_utils import GSCUtils, GSCUtilsMisc, GSCChecks
        from utilities.text_conversions import PokemonNamesForGen
        GSCUtils()

        kor_mon_example = GSCUtilsMisc.read_data(self.get_path(self.kor_mon_example_path))
        self.assertFalse(kor_mon_example is None)

        checks = GSCChecks([0,0,0], True)
        mon = GSCUtils.single_mon_from_data_multilanguage(checks, kor_mon_example)
        real_mon = mon[0]
        is_egg = mon[1]
        base_ot_name_values = real_mon.ot_name.values[:]
        base_nickname_values = real_mon.nickname.values[:]
        self.assertTrue(real_mon.ot_name.values == base_ot_name_values)
        self.assertTrue(real_mon.nickname.values == base_nickname_values)

        real_mon.patch_out_bad_chars_for_language_buffered_only(PokemonNamesForGen.ENGLISH_LANGUAGE, checks, is_egg)
        self.assertTrue(real_mon.ot_name.values != base_ot_name_values)
        self.assertTrue(real_mon.nickname.values != base_nickname_values)

        real_mon.apply_all_text_transforms_to_all(PokemonNamesForGen.KOREAN_LANGUAGE)
        self.assertTrue(real_mon.ot_name.values == base_ot_name_values)
        self.assertTrue(real_mon.nickname.values == base_nickname_values)

    def test_mon_kor_to_jpn_back(self):
        """
        Check that all the possible (5) characters get converted back and forth properly...
        """
        sys.path.append(sys.path[0] + '/..')

        from utilities.gsc_trading_data_utils import GSCUtils, GSCUtilsMisc, GSCChecks
        from utilities.text_conversions import PokemonNamesForGen
        GSCUtils()

        kor_mon_example = GSCUtilsMisc.read_data(self.get_path(self.kor_mon_example_path))
        self.assertFalse(kor_mon_example is None)

        checks = GSCChecks([0,0,0], True)
        mon = GSCUtils.single_mon_from_data_multilanguage(checks, kor_mon_example)
        real_mon = mon[0]
        is_egg = mon[1]
        base_ot_name_values = real_mon.ot_name.values[:]
        base_nickname_values = real_mon.nickname.values[:]
        self.assertTrue(real_mon.ot_name.values == base_ot_name_values)
        self.assertTrue(real_mon.nickname.values == base_nickname_values)

        real_mon.patch_out_bad_chars_for_language_buffered_only(PokemonNamesForGen.JAPANESE_LANGUAGE, checks, is_egg)
        for i in range(GSCUtils.jpn_name_len, len(real_mon.ot_name.values)):
            # Simulate the truncation that happens due to trades
            real_mon.ot_name.values[i] = GSCUtils.end_of_line
        for i in range(GSCUtils.jpn_name_len, len(real_mon.nickname.values)):
            # Simulate the truncation that happens due to trades
            real_mon.nickname.values[i] = GSCUtils.end_of_line
        self.assertTrue(real_mon.ot_name.values != base_ot_name_values)
        self.assertTrue(real_mon.nickname.values != base_nickname_values)

        real_mon.apply_all_text_transforms_to_all(PokemonNamesForGen.KOREAN_LANGUAGE)
        self.assertTrue(real_mon.ot_name.values[:GSCUtils.jpn_name_len] == base_ot_name_values[:GSCUtils.jpn_name_len])
        self.assertTrue(real_mon.nickname.values[:GSCUtils.jpn_name_len] == base_nickname_values[:GSCUtils.jpn_name_len])

    def test_mon_jpn_to_kor_back(self):
        """
        Check that all characters get converted back and forth properly...
        """
        sys.path.append(sys.path[0] + '/..')

        from utilities.gsc_trading_data_utils import GSCUtils, GSCUtilsMisc, GSCChecks
        from utilities.text_conversions import PokemonNamesForGen
        GSCUtils()

        jpn_mon_example = GSCUtilsMisc.read_data(self.get_path(self.jpn_mon_example_path))
        self.assertFalse(jpn_mon_example is None)

        checks = GSCChecks([0,0,0], True)
        mon = GSCUtils.single_mon_from_data_multilanguage(checks, jpn_mon_example)
        real_mon = mon[0]
        is_egg = mon[1]
        base_ot_name_values = real_mon.ot_name.values[:]
        base_nickname_values = real_mon.nickname.values[:]
        self.assertTrue(real_mon.ot_name.values == base_ot_name_values)
        self.assertTrue(real_mon.nickname.values == base_nickname_values)

        real_mon.patch_out_bad_chars_for_language_buffered_only(PokemonNamesForGen.KOREAN_LANGUAGE, checks, is_egg)
        self.assertTrue(real_mon.ot_name.values != base_ot_name_values)
        self.assertTrue(real_mon.nickname.values != base_nickname_values)

        real_mon.apply_all_text_transforms_to_all(PokemonNamesForGen.JAPANESE_LANGUAGE)
        self.assertTrue(real_mon.ot_name.values == base_ot_name_values)
        self.assertTrue(real_mon.nickname.values == base_nickname_values)

    def test_mon_en_to_kor_back(self):
        """
        Check that all characters get converted back and forth properly...
        """
        sys.path.append(sys.path[0] + '/..')

        from utilities.gsc_trading_data_utils import GSCUtils, GSCUtilsMisc, GSCChecks
        from utilities.text_conversions import PokemonNamesForGen
        GSCUtils()

        en_mon_example = GSCUtilsMisc.read_data(self.get_path(self.en_mon_example_path))
        self.assertFalse(en_mon_example is None)

        checks = GSCChecks([0,0,0], True)
        mon = GSCUtils.single_mon_from_data_multilanguage(checks, en_mon_example)
        real_mon = mon[0]
        is_egg = mon[1]
        base_ot_name_values = real_mon.ot_name.values[:]
        base_nickname_values = real_mon.nickname.values[:]
        self.assertTrue(real_mon.ot_name.values == base_ot_name_values)
        self.assertTrue(real_mon.nickname.values == base_nickname_values)

        real_mon.patch_out_bad_chars_for_language_buffered_only(PokemonNamesForGen.KOREAN_LANGUAGE, checks, is_egg)
        self.assertTrue(real_mon.ot_name.values == base_ot_name_values)
        self.assertTrue(real_mon.nickname.values == base_nickname_values)

        real_mon.apply_all_text_transforms_to_all(PokemonNamesForGen.ENGLISH_LANGUAGE)
        self.assertTrue(real_mon.ot_name.values == base_ot_name_values)
        self.assertTrue(real_mon.nickname.values == base_nickname_values)

    def test_mon_en_old_load(self):
        """
        Check that all characters get converted back and forth properly...
        """
        sys.path.append(sys.path[0] + '/..')

        from utilities.gsc_trading_data_utils import GSCUtils, GSCUtilsMisc, GSCChecks
        from utilities.text_conversions import PokemonNamesForGen
        GSCUtils()

        en_mon_example = GSCUtilsMisc.read_data(self.get_path(self.en_old_mon_example_path))
        self.assertFalse(en_mon_example is None)

        checks = GSCChecks([0,0,0], True)
        mon = GSCUtils.single_mon_from_data_multilanguage(checks, en_mon_example)
        real_mon = mon[0]
        is_egg = mon[1]

    def get_path(self, target):
        return self.base_folder + target

if __name__ == "__main__":
    unittest.main()
