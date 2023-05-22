# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

### [Unreleased]

### [1.1.0] - 2023-05-22

#### Added

- :sparkles: Added documentation about required configuration when using
  Chromecast w/ GoogleTV devices
- :sparkles: Add ability to customize background image brightness
- :sparkles: Switch to custom Chromecast receiver app
- :sparkles: Dynamically determine local IP address when contacting Chromecast.
  This should make the app more robust when the local IP address changes.

#### Fixed

- :bug: Fix crash at startup w/ non-existant config file
- :bug: Enqueue startlists to be processed in main thread to avoid tkinter error

### [1.0.1] - 2023-02-10

#### Fixed

- :bug: Decrease image refresh interval to prevent Chromecast timeout

### [1.0.0] - 2023-02-05

#### Changed

- :information_source: Major overhaul of UI and code structure

### [0.8.1] - 2022-07-19

#### Fixed

- :bug: Properly determine start list filenames for event numbers &lt; 100

### [0.8.0] - 2022-07-03

#### Added

- :sparkles: Swimmer names that are too long to display are automatically
  shortened
- :sparkles: Added documentation for using Wahoo Results with Meet Maestro

#### Fixed

- :bug: Fix sorting of event numbers when writing dolphin CSV.

### [0.7.0] - 2022-06-23

#### Fixed

- :bug: Gracefully handle Chromecast removal messages from untracked devices

#### Added

- :sparkles: Application now has a startup splash screen
- :sparkles: Waiting screen now uses the specified background image

#### Changed

- :information_source: Application now has a new icon
- :information_source: Executable is now built w/ UPX enabled to decrease the
  size of the binary.

### [0.6.2] - 2022-05-14

#### Fixed

- :bug: Properly disconnect from Chromecasts when probing to prevent leaking
  threads

### [0.6.1] - 2022-01-17

#### Fixed

- :bug: Catch and report errors if config file isn't writable

### [0.6.0] - 2021-08-15

#### Added

- :sparkles: Added new screen to manually select a previous result, change its
  event/heat and re-publish it.
- :sparkles: Integrated Sentry.io for crash reporting

### [0.5.0] - 2021-07-24

#### Added

- :sparkles: The scoreboard now has Chromecast support.
- :sparkles: The latest results are shown in the application.

#### Fixed

- :bug: The text file encoding for `scb`, `do4`, and `csv` files was left
  unspecified, which potentially led to decoding problems when non-ASCII
  characters were encountered. `cp1252` is now specified directly.

#### Removed

- :skull_and_crossbones: Removed support for "windowed" and full screen (on an
  attached monitor) scoreboard output

### [0.4.1] - 2021-06-19

#### Fixed

- :bug: Fixed parsing of do4 file containing empty event number. This caused
  the scoreboard to stop displaying results after an empty event number was
  encountered.

### [0.4.0] - 2021-04-24

#### Added

- :sparkles: Add update notification

#### Changed

- :information_source: Releases will now be signed zips instead of bare exe files to avoid warnings on download and allow authentication of releases

### [0.3.2] - 2021-01-16

#### Fixed

- :bug: Fixed fullscreen only working on primary display
- :bug: Fixed hang when background image is not found

### [0.3.1] - 2020-12-04

#### Fixed

- :bug: Fixed handling of bool as int

### [0.3.0] - 2020-12-03

#### Added

- :sparkles: Option to suppress final time if the individual times have >0.3s spread
- :sparkles: Option to run the scoreboard in fullscreen mode

#### Fixed

- :bug: Properly display results when start list file is missing
- :bug: Fix incorrect final time calculation

### [0.2.0] - 2020-10-25

#### Added

- :sparkles: Number of lanes can be customized within the application
- :sparkles: Many new scoreboard configuration options: Fonts, colors, and background image
- :sparkles: Custom colors for 1st-3rd place
- :sparkles: Test button to show a scoreboard mockup demonstrating the current customization settings

#### Changed

- :information_source: (internal) Switched from using widgets for the scoreboard to placing text on a Canvas object

#### Fixed

- :bug: There were instances where the incorrect final time was calculated due to imprecision in floating point arithmetic

### [0.1.0] - 2020-09-06

#### Added

- Initial release

[Unreleased]: https://github.com/JohnStrunk/wahoo-results/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/JohnStrunk/wahoo-results/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/JohnStrunk/wahoo-results/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/JohnStrunk/wahoo-results/compare/v0.8.1...v1.0.0
[0.8.1]: https://github.com/JohnStrunk/wahoo-results/compare/v0.8.0...v0.8.1
[0.8.0]: https://github.com/JohnStrunk/wahoo-results/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/JohnStrunk/wahoo-results/compare/v0.6.2...v0.7.0
[0.6.2]: https://github.com/JohnStrunk/wahoo-results/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/JohnStrunk/wahoo-results/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/JohnStrunk/wahoo-results/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/JohnStrunk/wahoo-results/compare/v0.4.1...v0.5.0
[0.4.1]: https://github.com/JohnStrunk/wahoo-results/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/JohnStrunk/wahoo-results/compare/v0.3.2...v0.4.0
[0.3.2]: https://github.com/JohnStrunk/wahoo-results/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/JohnStrunk/wahoo-results/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/JohnStrunk/wahoo-results/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/JohnStrunk/wahoo-results/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/JohnStrunk/wahoo-results/releases/tag/v0.1.0
