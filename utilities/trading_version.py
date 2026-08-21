class TradingVersion:
    """
    Class which contains the version and the version's helper methods.
    """

    # Changes each protocol change
    version_major = 4
    version_minor = 1
    version_build = 0

    # Fixed, does not change
    first_battle_version_major = 4
    first_battle_version_minor = 1
    first_battle_version_build = 0

    def read_version_data(data):
        ret = []
        for i in range(3):
            ret += [data[i * 2] + (data[(i * 2) + 1] << 8)]
        return ret
    
    def prepare_version_data():
        ret = []
        ret += [TradingVersion.version_major & 0xFF, (TradingVersion.version_major >> 8) & 0xFF]
        ret += [TradingVersion.version_minor & 0xFF, (TradingVersion.version_minor >> 8) & 0xFF]
        ret += [TradingVersion.version_build & 0xFF, (TradingVersion.version_build >> 8) & 0xFF]
        return ret

    def is_version_greater_equal_than(parsed_data, major, minor, build):
        if parsed_data is None:
            return False
        if parsed_data[0] < major:
            return False
        if parsed_data[1] < minor:
            return False
        if parsed_data[2] < build:
            return False
        return True

    def is_version_lesser_equal_than(parsed_data, major, minor, build):
        if parsed_data is None:
            return True
        if parsed_data[0] > major:
            return False
        if parsed_data[1] > minor:
            return False
        if parsed_data[2] > build:
            return False
        return True

    def is_version_greater_than(parsed_data, major, minor, build):
        return not TradingVersion.is_version_lesser_equal_than(parsed_data, major, minor, build)

    def is_version_lesser_than(parsed_data, major, minor, build):
        return not TradingVersion.is_version_greater_equal_than(parsed_data, major, minor, build)

    def is_version_equal_to(parsed_data, major, minor, build):
        return TradingVersion.is_version_greater_equal_than(parsed_data, major, minor, build) and TradingVersion.is_version_lesser_equal_than(parsed_data, major, minor, build)

    def is_version_battle_compatible(parsed_data):
        return TradingVersion.is_version_greater_equal_than(parsed_data, TradingVersion.first_battle_version_major, TradingVersion.first_battle_version_minor, TradingVersion.first_battle_version_build)
