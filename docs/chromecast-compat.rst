.. include:: common.rst
========================
Chromecast compatibility
========================

Google has made several different versions of it's Chromecast line of devices.
The table below summarizes their support status in |wr|.

+-------------------------------------+-------------------------------------+
| Chromecast device                   | Compatibility                       |
+-------------------------------------+-------------------------------------+
|  .. figure:: media/cc-gen1.jpg      | Working ✅                          |
|     :figwidth: 50 %                 |                                     |
|     :align: center                  |                                     |
|                                     |                                     |
|     First generation [#g1]_         |                                     |
+-------------------------------------+-------------------------------------+
|  .. figure:: media/cc-gen2.jpg      | Untested, but should work 🤞        |
|     :figwidth: 50 %                 |                                     |
|     :align: center                  |                                     |
|                                     |                                     |
|     Second generation [#g2]_        |                                     |
+-------------------------------------+-------------------------------------+
|  .. figure:: media/cc-gen3.jpg      | Working ✅                          |
|     :figwidth: 50 %                 |                                     |
|     :align: center                  |                                     |
|                                     |                                     |
|     Third generation [#g3]_         |                                     |
+-------------------------------------+-------------------------------------+
|  .. figure:: media/cc-gtv.jpg       | Configuration required ⚠️           |
|     :figwidth: 50 %                 |                                     |
|     :align: center                  | (`see below <#gtvcfg>`_)            |
|                                     |                                     |
|     Chromecast w/ Google TV [#gtv]_ |                                     |
+-------------------------------------+-------------------------------------+

Required configuration changes
==============================

.. _gtvcfg:

Chromecast w/ Google TV
    In their default configuration, the Chromecast w/ Google TV devices will
    timeout after 10 minutes and return to "ambient mode." To prevent this, a
    few settings must be changed:

    1. Disable power saving

       - Go to Settings (⚙️ icon) > System > Power & Energy
       - Set "Turn off display" to "Never"

    2. Enable "developer mode"

       - Go to Settings (⚙️ icon) > System > About
       - Scroll down to "Android TV OS Build" and repeatedly click on it until
         you get the message "You are now a developer"

    3. Enable "Stay awake"

       - Go to Settings (⚙️ icon) > System > Developer options
       - Enable "Stay awake"

-----

.. [#g1] Image attribution: `© Raimond Spekking / CC BY-SA 4.0 <https://en.wikipedia.org/wiki/File:Chromecast_(1st_generation)-0869.jpg>`__
.. [#g2] Image attribution: `© Y2kcrazyjoker4 / CC BY-SA 4.0 <https://en.wikipedia.org/wiki/File:Chromecast-2015.jpg>`__
.. [#g3] Image attribution: `© Qurren / CC BY-SA 4.0 <https://en.wikipedia.org/wiki/File:Chromecast_(3rd_generation).jpg>`__
.. [#gtv] Image attribution: `© Y2kcrazyjoker4 / CC BY-SA 4.0 <https://en.wikipedia.org/wiki/File:Chromecast-with-Google-TV-snow-color-on-wood-table2.jpg>`__
