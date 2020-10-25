# Wahoo! Results

Wahoo! Results is a scoreboard for displaying swimming meet race results.

If you are looking for a way to have a scoreboard to display race results and
you use Meet Manager + a CTS Dolphin system to run your meets, this may be for
you!

![Example scoreboard](docs/media/demo1.png)

## Requirements

- Hy-Tek Meet Manager - Used to generate the scoreboard "start list" files
- Colorado Dolphin timing - Used to gather the timing information
- A Windows PC to run Wahoo! Results

## Features

- Configurable number of lanes: 6 - 10
- Customizable text fonts, sizes, and colors
- Custom background images, or just use a solid color
- Calculates final time based on multiple Dolphin watches

## Installation

Download the latest version of `wahoo-results.exe` from the [releases
page](https://github.com/JohnStrunk/wahoo-results/releases).

The program a single executable w/ no installation necessary. Configuration
preferences are saved into a `wahoo-results.ini` file in the same directory.

## How it works

1. Once the meet has been seeded in Meet Manager, export CTS start list files
   as you would for a normal scoreboard.
2. Use Wahoo! Results to generate the event file for the Dolphin software
   based on the start list files.
3. Configure Wahoo! Results to watch for the Dolphin `*.do4` race result
   files.
4. Run the scoreboard. It will display race results including both names (from
   the start list files) and times (from the Dolphin result files).

## License

This software is licensed under the GNU Affero General Public License version
3. See the [LICENSE](LICENSE) file for full details.