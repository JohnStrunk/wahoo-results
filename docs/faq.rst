.. include:: common.rst
===================
FAQ/Troubleshooting
===================

Having problems?

I'm not getting any results.
    The scoreboard displays race results when a new ``DO4`` file appears in
    the configured log directory.

    #. Ensure the Dolphin software is :ref:`configured to generate
       <config_dolphin_sw>` ``DO4`` files in addition to any other type of log
       file you may be using.
    #. Ensure |wr| is configured to :ref:`watch the correct log directory
       <set_results_dir>`.
I get results, but none of the swimmer's names are displayed.
    The scoreboard is not able to find a corresponding start list for the
    event/heat.

    #. Ensure the Event and Heat number of the race are displayed correctly.
    #. Ensure |wr| is looking for the :ref:`start lists in the correct directory <set_start_list_dir>`.
The event and heat number are wrong.
    The event and heat number are read from the ``DO4`` result file. Ensure
    the Dolphin software displays the correct event and heat number for each
    race.

Question still not answered? `Open an issue on GitHub. <https://github.com/JohnStrunk/wahoo-results/issues>`_