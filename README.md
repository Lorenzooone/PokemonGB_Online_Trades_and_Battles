# PokemonGB_Online_Trades_and_Battles
This is an overlay for Pokémon Red/Blue/Yellow, Gold/Silver/Crystal and Ruby/Sapphire/Emerald/Fire Red/Leaf Green which aims at adding Online Trading and Battle support.
It also adds Online Trading support to Pokémon Ruby/Sapphire/Emerald/Fire Red/Leaf Green.

The project currently includes a server (serving.py) and two clients (`emulator_trade_battle.py` and `usb_trade_battle.py`). Clients connect a local game to the server. The server provides "rooms" to communicate between games connected to two different clients. It also hosts a "pool" that you can trade with individually, with no need to coordinate with a partner.

The clients run from the terminal and connect a game to a server. Two interfaces are currently available:
 * `usb_trade_battle.py` connects to real gameboy hardware via a GB Link Cable to USB Adapter
 * `emulator_trade_battle.py` connects to the BGB emulator

The software focuses on safety for the end Device's data (more on that later) and speed (by having some optimizations put in place).

## Features
### 2-Player Trade and Battles
Register to a server's room and trade/battle with another player, just like you would in person!

#### Comunication Modes
The program supports both a Synchronized mode, in which a single byte at a time is exchanged (just like when using the original Link Cable), and a Buffered mode.

When using Buffered mode, the players have to initialize a fake trade/battle (which the program will automatically close) in order to prepare their own data.
Once the data is ready, a single transfer will send it to the other player, who will be able to start the actual trade/battle using it.
This comunication mode, although slower, can be safer if one of the players has connectivity issues.

### Pool Trade
Exchange your Pokémon with one at random from the Server's Pool, and make it available for other players!

### Safety First
Each byte which is sent to your Device is cleaned using Sanity Checks. They make sure your game doesn't crash due to another player's actions.

Said checks can also be removed, if one so chooses.

## Usage
### Installing the dependencies
Python >= 3.6.1 is required in order to run this.

Required packages are found inside requirements_local.txt.

They can be installed by using `pip install -r requirements_local.txt`.

Alternatively, `python -m pip install -r requirements_local.txt` can also be used.

Optionally, a virtual environment may be setup with `python -m venv local_env ; source local_env/bin/activate`.

### Running the Client
You can start the client running at any time; feel free to start it before you have your game ready to trade.
Invoke the correct client:

#### Using the GB Link Cable to USB Adapter
Run `python ./usb_trade_battle.py`.
If the adapter is inserted, it should be detected.

*NB*: If you want to trade between an emulator and physical hardware, it seems to be more stable if you connect the GBLink adaptor with this CLI client instead of the web client available in the GBLink launcher.

#### Using BGB
Run `python ./emulator_trade_battle.py`.
Once you're out of the program's menu, and you have started BGB, you can then left click on the actively running BGB window, and click Link->Connect->Ok.
It should connect to the emulator, once that is done.

*Note*
If you want to trade emulator-to-emulator, run two instances of `emulator_trade_battle.py` but specify a different port for the emulator to connect to with the `-ep` flag, then add that port to the end of the connection string after you click "Link->Connect" in BGG -- `127.0.0.1:6543`, if you specified port 6543).

However it's simpler to link the two BGB instances together using "Link->Listen" in one and "Link->Connect" in the other.

### Client Options
The clients have a variety of flags to adjust their behavior instead of going through the menus every time. Invoke the client with the `-h` flag to see usage info:

```
  -h, --help            show this help message and exit
  -btl, --battle        Do a battle
  -g, --generation GEN_NUMBER
                        generation (1 = RBY/Timecapsule, 2 = GSC, 3 = RSE Special)
  -t, --trade_type TRADE_TYPE
                        trade type (2P = 2-Player Trade, PT = Pool Trade)
  -r, --room ROOM       2-Player Trade's room
  -b, --buffered        default to buffered trading instead of synchronous
  -j, --japanese        use it if your game is Japanese
  -dsc, --disable_sanity_checks
                        don't perform sanity checks for data sent to the device
  -btt, --battle_turn_time TIME_BETWEEN_BATTLE_TURNS
                        Time between battle turns for generation 2
  -dkb, --disable_kill_drops
                        don't kill the process for dropped bytes
  -mlp, --max_level_pool MAX_LEVEL
                        Pool's max level
  -egp, --eggify_pool   turns Pool Pokémon into ready-to-hatch eggs
  -q, --quiet           don't print status messages to stdout
  -sh, --server_host SERVER_HOST
                        server's host
  -sp, --server_port SERVER_PORT
                        server's port
  -eh, --emulator_host EMULATOR_HOST
                        emulator's local host (only in emulator_trade_battle.py)
  -ep, --emulator_port EMULATOR_PORT
                        emulator's local port (only in emulator_trade_battle.py)
  -efc, --emu_fast_conn
                        enables fast emulator connection (only in emulator_trade_battle.py)
```

### Notes on Battles using Gen1 games

Please be careful about using the moves Counter, Mirror Move, Psywave, Fly , Dig and Mimic, as they may cause issues.
There may also be weird interactions with turn order (if you encounter any significant problem, please create an issue).

### Notes on Battles using Gen2 games
Between each turn the software waits a certain time before checking for user input (by default 30 seconds).

This is because checking for user input may cause connectivity issues when some battle animations and sounds are playing.

Enter can be pressed to skip the wait after an action is selected. If issues are encountered with this approach, please file an issue.

Please be careful about using the move Beat Up, as it may cause issues.
There may also be weird interactions with turn order (if you encounter any significant problem, please create an issue).

### Trading using Gen3 games
The software currently makes use of the [Pokemon-Gen3-to-GenX](https://github.com/Lorenzooone/Pokemon-Gen3-to-Gen-X) project to add support to trading using Pokémon Ruby/Sapphire/Emerald/Fire Red/Leaf Green.

As such, you must first multiboot into it using the "m" option. Then, you can select the Gen 3 option to trade.

If you're using the GB Link Cable to USB Adapter, updating to a reconfigurable firmware is EXTREMELY suggested for trading using Gen 3 games.
[One is available here](https://github.com/Lorenzooone/gb-link-firmware-reconfigurable/releases).

## Development
### Running the server locally
Required packages for running the server are found inside requirements_server.txt:

1. Set up a virtual environment: `python -m venv server_env; source server_env/bin/activate`
2. Install the dependencies: `pip install -r requirements_server.txt`
3. Run the server locally: `PORT=8080 python serving.py`
4. Connect a client: `python emulator_trade_battle.py -sh localhost -sp 8080`

The default trading pools are `pool_default_data/pool_mons*.bin`

Happy Hacking!
