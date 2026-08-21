import math
from .gsc_trading_data_utils import GSCUtils, GSCUtilsMisc

class PokemonTextConversions:
    """
    Class which handles sanity checks and cleaning of the received data.
    checks_map and single_pokemon_checks_map are its product used to apply
    the checks.
    """
    base_folder = "useful_data/text/"
    text_gen3_gen12_int_path = "text_gen3_to_gen12_int.bin"
    text_gen3_gen12_int_jp_path = "text_gen3_to_gen12_int_jp.bin"
    text_gen3_gen12_jp_path = "text_gen3_to_gen12_jp.bin"
    text_gen3_gen12_jp_int_path = "text_gen3_to_gen12_jp_int.bin"
    text_gen3_general_int_path = "text_gen3_to_general_int.bin"
    text_gen3_general_jp_path = "text_gen3_to_general_jp.bin"
    text_gen12_gen3_int_path = "text_gen12_to_gen3_int.bin"
    text_gen12_gen3_jp_path = "text_gen12_to_gen3_jp.bin"
    text_general_gen3_int_path = "text_general_to_gen3_int.bin"
    text_general_gen3_jp_path = "text_general_to_gen3_jp.bin"

    own_istance = None

    def __init__(self):
        self.utils_class = self.get_utils_class()
        self.gen3_gen12_int = (GSCUtilsMisc.read_data(self.get_path(self.text_gen3_gen12_int_path)))
        self.gen3_gen12_int_jp = (GSCUtilsMisc.read_data(self.get_path(self.text_gen3_gen12_int_jp_path)))
        self.gen3_gen12_jp = (GSCUtilsMisc.read_data(self.get_path(self.text_gen3_gen12_jp_path)))
        self.gen3_gen12_jp_int = (GSCUtilsMisc.read_data(self.get_path(self.text_gen3_gen12_jp_int_path)))
        self.gen3_general_int = (GSCUtilsMisc.read_data(self.get_path(self.text_gen3_general_int_path)))
        self.gen3_general_jp = (GSCUtilsMisc.read_data(self.get_path(self.text_gen3_general_jp_path)))
        self.gen12_gen3_int = (GSCUtilsMisc.read_data(self.get_path(self.text_gen12_gen3_int_path)))
        self.gen12_gen3_jp = (GSCUtilsMisc.read_data(self.get_path(self.text_gen12_gen3_jp_path)))
        self.general_gen3_int = (GSCUtilsMisc.read_data(self.get_path(self.text_general_gen3_int_path)))
        self.general_gen3_jp = (GSCUtilsMisc.read_data(self.get_path(self.text_general_gen3_jp_path)))
        PokemonTextConversions.own_istance = self

    def get_path(self, target):
        return self.base_folder + target

    def get_utils_class(self):
        return GSCUtils

    def convert_gen12_char_to_char(value, is_jp = False):
        if PokemonTextConversions.own_istance is None:
            PokemonTextConversions()
        self = PokemonTextConversions.own_istance
        conv_table1 = self.gen12_gen3_int
        conv_table2 = self.gen3_general_int
        if is_jp:
            conv_table1 = self.gen12_gen3_jp
            conv_table2 = self.gen3_general_jp
        out = chr(conv_table2[conv_table1[value]])
        return out

    def convert_char_to_gen12_char(value, is_jp = False):
        if PokemonTextConversions.own_istance is None:
            PokemonTextConversions()
        self = PokemonTextConversions.own_istance
        conv_table1 = self.general_gen3_int
        conv_table2 = self.gen3_gen12_int
        if is_jp:
            conv_table1 = self.general_gen3_jp
            conv_table2 = self.gen3_gen12_jp
        out = conv_table2[conv_table1[ord(value)]]
        return out

