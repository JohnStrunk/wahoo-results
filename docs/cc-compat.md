# Chromecast compatibility

Google has made several different versions of it's Chromecast line of devices.
The table below summarizes their support status in {{ WR }}:

<div class="mygrid" markdown>
<div class="mycard" markdown>

## First generation

:material-check-circle:{ .green } &ndash; Working

-----

![Gen 1](images/cc-gen1.jpg){ width=320 height=240 }

<sub>Image attribution: [© Raimond Spekking / CC BY-SA 4.0](https://en.wikipedia.org/wiki/File:Chromecast_(1st_generation)-0869.jpg)<sub>
</div>
<div class="mycard" markdown>

## Second generation

:material-sign-caution:{ .yellow } &ndash; Untested, but should work

-----

![Gen 2](images/cc-gen2.jpg){ width=306 height=240 }

<sub>Image attribution: [© Y2kcrazyjoker4 / CC BY-SA 4.0](https://en.wikipedia.org/wiki/File:Chromecast-2015.jpg)</sub>
</div>
<div class="mycard" markdown>

## Third generation

:material-check-circle:{ .green } &ndash; Working

-----

![Gen 3](images/cc-gen3.jpg){ width=240 height=240 }

<sub>Image attribution: [© Qurren / CC BY-SA 4.0](https://en.wikipedia.org/wiki/File:Chromecast_(3rd_generation).jpg)</sub>
</div>
<div class="mycard" markdown>

## Chromecast w/ Google TV

<!-- markdownlint-disable-next-line MD051 -->
:material-wrench:{ .red } &ndash; [Configuration required](#config-ccwtgv)

-----

![CC w/ GTV](images/cc-gtv.jpg){ width=320 height=213 }

<sub>Image attribution: [© Y2kcrazyjoker4 / CC BY-SA 4.0](https://en.wikipedia.org/wiki/File:Chromecast-with-Google-TV-snow-color-on-wood-table2.jpg)</sub>
</div>
</div>

## Required configuration changes

### Chromecast w/ Google TV { #config-ccwtgv }

In their default configuration, the Chromecast w/ Google TV devices will timeout
after 10 minutes and return to "ambient mode." To prevent this, a few settings
must be changed:

1. Disable power saving
    - Go to Settings (:material-cog: icon) :material-chevron-right: System
      :material-chevron-right: Power & Energy
    - Set "Turn off display" to "Never"

1. Enable "developer mode"

    - Go to Settings (:material-cog: icon) :material-chevron-right: System
      :material-chevron-right: About
    - Scroll down to "Android TV OS Build" and repeatedly click on it until
        the message "You are now a developer" appears

1. Enable "Stay awake"

    - Go to Settings (:material-cog: icon) :material-chevron-right: System
      :material-chevron-right: Developer options
    - Enable "Stay awake"
