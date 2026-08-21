# PokemonGB_Online_Trades_and_Battles
This is an overlay for Pokémon Red/Blue/Yellow, Gold/Silver/Crystal and Ruby/Sapphire/Emerald/Fire Red/Leaf Green which aims at adding Online Trading and Battle support.
It also adds Online Trading support to Pokémon Ruby/Sapphire/Emerald/Fire Red/Leaf Green.

Two interfaces are currently available. One for a GB Link Cable to USB Adapter, and the other for BGB.

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

## Installing the prerequisite packages
Python >= 3.6 is required in order to run this.

Required packages are found inside requirements.txt.

They can be installed by using `pip install -r requirements.txt`.

## Using the GB Link Cable to USB Adapter
Run `python ./usb_trade_battle.py`.
If the adapter is inserted, it should be detected.

## Using BGB
Run `python ./emulator_trade_battle.py`.
Once you're out of the program's menu, and you have started BGB, you can then left click on the actively running BGB window, and click Link->Connect->Ok.
It should connect to the emulator, once that is done.

## Notes on Battles using Gen1 games

Please be careful about using the moves Counter, Mirror Move, Psywave, Fly , Dig and Mimic, as they may cause issues.
There may also be weird interactions with turn order (if you encounter any significant problem, please create an issue).

## Notes on Battles using Gen2 games
Between each turn the software waits a certain time before checking for user input (by default 30 seconds).

This is because checking for user input may cause connectivity issues when some battle animations and sounds are playing.

Enter can be pressed to skip the wait after an action is selected. If issues are encountered with this approach, please file an issue.

Please be careful about using the move Beat Up, as it may cause issues.
There may also be weird interactions with turn order (if you encounter any significant problem, please create an issue).

## Trading using Gen3 games
The software currently makes use of the [Pokemon-Gen3-to-GenX](https://github.com/Lorenzooone/Pokemon-Gen3-to-Gen-X) project to add support to trading using Pokémon Ruby/Sapphire/Emerald/Fire Red/Leaf Green.

As such, you must first multiboot into it using the "m" option. Then, you can select the Gen 3 option to trade.

If you're using the GB Link Cable to USB Adapter, updating to a reconfigurable firmware is EXTREMELY suggested for trading using Gen 3 games.
[One is available here](https://github.com/Lorenzooone/gb-link-firmware-reconfigurable/releases).
