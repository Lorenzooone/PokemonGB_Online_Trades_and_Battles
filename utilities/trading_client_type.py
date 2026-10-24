class TradingClientType:
    """
    Class which contains the client type and the client type's helper methods.
    """

    python_usb = 1
    python_emu_bgb = 2
    python_server = 3
    js_usb = 4
    js_emu_bgb = 5

    clients_text = {
        python_usb: "Python USB",
        python_emu_bgb: "Python Emulator BGB",
        python_server: "Python Server",
        js_usb: "JS USB",
        js_emu_bgb: "JS Emulator BGB",
    }

    def get_text_for_client_type(client_type):
        if client_type in TradingClientType.clients_text.keys():
            return TradingClientType.clients_text[client_type]
        return "Unknown"

