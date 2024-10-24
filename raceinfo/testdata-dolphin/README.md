# Dolphin test data

This directory contains test data taken from the CTS Dolphin timing system. This
is data that has been taken to cover specific test scenarios. For each test
case, the data is captured in all of the formats that the Dolphin system
supports.

The data was captured using the following versions:

- Software version: 5.0.19.0
- Base firmware: 1.51
- Starter firmware: 1.31
- Watch firmware: 1.51

## Event data

Each event in the dolphin software has the following properties:

- Event number: 0-6 alphanumeric characters
- Event name: 0-25 alphanumeric characters
- Round: A single character (A)ll, (P)relim, (F)inal
- Heats: Number of heats 1-99
- Splits: 1-10

Each race result is also associated with:

- Meet number: numeric, incremented each time the software is started
- Race number: numeric, starts at 1 and increments with each race

## Data formats

The data is stored in the following formats:

- `*.csv`: CTS Dolphin CSV format
- `*.do3`: CTS Dolphin native format without splits
- `*.do4`: CTS Dolphin native format with splits
- `*.txt`: CTS Dolphin text format
- `*.xml`: CTS Dolphin XML format

**TODO:** Describe file naming for each format.

## Test scenarios

The goal of these scenarios is to cover the variations that are possible in the
results to ensure we can correctly parse the data.

| Description | Meet | Race(s) |
|-------------|-----:|--------:|
| Races w/ missing times | 8 | 1-2 |
| Lanes marked empty or DQ | 8 | 3 |
| Races with (missing) splits | 8 | 4-6 |
| Event names | 8 | 7 |
| Rounds | 8 | 8-9 |
| No events loaded | 8 | 10 |
| 0-9 lane numbering | 8 | 11-12 |
| No events loaded | 9 | 1-3 |
| Races with extra splits | 9 | 4,6 |

- Races w/ missing times: This covers all combinations of 0 through 3 times per
  lane.
- Lanes marked empty or DQ: This covers scenarios where lanes are marked as
  EMPTY (either via the console or via the watch). It also covers scenarios
  where lanes are marked as DQ via the console.
- Races with splits: This covers scenarios where intermediate splits are present
  in the data, including cases where splits were missed.
- 0-9 lane numbering: This covers scenarios where the lane numbering is 0-9
  instead of the normal 1-10.
- No events loaded: This covers the scenario where no events are configured in
  the software.
- Rounds: This covers scenarios where the round is set to A, P, or F.
- Event names: This covers scenarios with special characters in the event name.
  Only "-" and "&" are supported.
