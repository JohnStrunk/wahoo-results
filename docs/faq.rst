.. include:: common.rst
===================
FAQ/Troubleshooting
===================

Having problems?

I'm not getting any results.
    The scoreboard displays race results when a new ``DO4`` file appears in
    the configured log directory.

    #. Ensure the Dolphin software is :ref:`configured to generate
       <qs_config_do4>` ``DO4`` files in addition to any other type of log
       file you may be using.
    #. Ensure |wr| is configured to :ref:`watch the correct log directory
       <qs_set_result_dir>`.
I get results, but none of the swimmer's names are displayed.
    The scoreboard is not able to find a corresponding start list for the
    event/heat.

    #. Ensure the Event and Heat number of the race are displayed correctly.
    #. Ensure |wr| is looking for the :ref:`start lists in the correct directory <qs_set_start_dir>`.
The event and heat number are wrong.
    The event and heat number are read from the ``DO4`` result file. Ensure
    the Dolphin software displays the correct event and heat number for each
    race.
My Chromecast devices aren't being discovered.
    When the application starts, it can take several seconds to discover the
    Chromecasts on the local network. If your device still doesn't appear
    after a minute or two, it may not be discoverable due to your facility's
    network configuration.

    One way to troubleshoot further is to see if you can `cast a Google
    Chrome web browser tab to the device
    <https://support.google.com/chromecast/answer/3228332?hl=en&co=GENIE.Platform%3DDesktop>`_.
    If you are unable to cast from Chrome, it is unlikely that |wr| is going
    to be able to find the device.

I've selected the Chromecast(s), but no image is being sent.
    Make sure that |wr| is not being blocked by Windows Firewall. The
    Chromecast protocol works by sending a web URL to the chromecast device,
    then the device fetches the actual media from that address. This means
    that |wr| runs an embedded web server that server must be accessible to
    the chromecast devices.

The Chromecast screen turns off or goes back to "ambient" (slideshow) mode periodically.
    You're probably using a Chromecast w/ Google TV... Those devices need some
    :doc:`configuration changes <chromecast-compat>` to work well with
    |wr|.

Question still not answered? `Feel free to ask on GitHub. <https://github.com/JohnStrunk/wahoo-results/discussions/categories/q-a>`_
