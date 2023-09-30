# FAQ/Troubleshooting

## I'm not getting any results.

The scoreboard displays race results when a new `DO4` file appears in the
configured log directory.

1. Ensure the Dolphin software is [configured to
   generate](quickstart.md#configure-result-files) `DO4` files in addition to
   any other type of log file you may be using.
1. Ensure {{ WR }} is configured to [watch the correct log
   directory](quickstart.md#set-the-results-directory).

## I get results, but none of the swimmer's names are displayed.

The scoreboard is not able to find a corresponding start list for the
event/heat.

1. Ensure the Event and Heat number of the race are displayed correctly.
1. Ensure {{ WR }} is looking for the [start lists in the correct
   directory](quickstart.md#set-the-start-list-directory).

## The event and heat number are wrong.

The event and heat number are read from the `DO4` result file. Ensure the
Dolphin software displays the correct event and heat number for each race.

## My Chromecast devices aren't being discovered.

When the application starts, it can take several seconds to discover the
Chromecasts on the local network. If your device still doesn't appear after a
minute or two, it may not be discoverable due to your facility's network
configuration.

One way to troubleshoot further is to see if you can [cast a Google Chrome web
browser tab to the
device](https://support.google.com/chromecast/answer/3228332?hl=en&co=GENIE.Platform%3DDesktop).
If you are unable to cast from Chrome, it is unlikely that {{ WR }} is going to
be able to find the device.

## I've selected the Chromecast(s), but no image is being sent.

Make sure that {{ WR }} is not being blocked by Windows Firewall. The Chromecast
protocol works by sending a web URL to the chromecast device, then the device
fetches the actual media from that address. This means that {{ WR }} runs an
embedded web server that server must be accessible to the chromecast devices.

## The Chromecast screen turns off or goes back to "ambient" (slideshow) mode periodically.

You're probably using a Chromecast w/ Google TV... Those devices need some
[configuration changes](cc-compat.md) to work well with {{ WR }}.

-----

**Question still not answered?** [Feel free to ask on
GitHub](https://github.com/JohnStrunk/wahoo-results/discussions/categories/q-a).
