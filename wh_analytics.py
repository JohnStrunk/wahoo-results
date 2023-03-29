# Wahoo! Results - https://github.com/JohnStrunk/wahoo-results
# Copyright (C) 2020 - John D. Strunk
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

'''Application usage analytics'''

import locale
import platform
from pprint import pprint
import socket
import time
from typing import Any, Dict, Optional, Tuple
import requests

from segment import analytics  # type: ignore
import sentry_sdk
import ipinfo  # type: ignore

from model import Model
import version

_CONTEXT: Dict[str, Any] = {}

def application_start(model: Model, screen_size: Tuple[int, int]) -> None:
    """Event for application startup"""
    analytics.write_key = version.SEGMENT_WRITE_KEY
    analytics.send = model.analytics.get()
    global _CONTEXT  # pylint: disable=global-statement
    _CONTEXT = {
        "context": _setup_context(screen_size),
        "race_count": 0,
        "race_count_with_names": 0,
        "session_start": time.time(),
        "user_id": model.client_id.get()
    }

    analytics.identify(
        user_id = _CONTEXT["user_id"],
        context = _CONTEXT["context"],
        traits = _CONTEXT["context"]["traits"],
    )
    _send_event("Scoreboard started")

def application_stop(model: Model) -> None:
    """Event for application shutdown"""
    _send_event("Scoreboard stopped", {
        "runtime": time.time() - _CONTEXT["session_start"],
        "race_count": _CONTEXT["race_count"],
        "race_count_with_names": _CONTEXT["race_count_with_names"],
        "lane_count": model.num_lanes.get(),
        "time_threshold": model.time_threshold.get(),
        "min_times": model.min_times.get(),
        "bg_image": model.image_bg.get() != "",
        "normal_font": model.font_normal.get(),
        "time_font": model.font_time.get(),
    })
    analytics.shutdown()

def results_received(has_names: bool, chromecasts: int) -> None:
    """Event for race results"""
    _CONTEXT["race_count"] += 1
    if has_names:
        _CONTEXT["race_count_with_names"] += 1
    _send_event("Results received", {
        "has_names": has_names,
        "chromecast_count": chromecasts
    })

def documentation_link() -> None:
    """Follow link to docs event"""
    _send_event("Documentation click")

def update_link() -> None:
    """Follow link to dl latest version event"""
    _send_event("DownloadUpdate click")

def set_cts_directory(changed: bool) -> None:
    """Set CTS start list directory"""
    _send_event("Browse CTS directory",{
        "directory_changed": changed,
    })

def wrote_dolphin_csv(num_events: int) -> None:
    """Dolphin CSV event list written"""
    _send_event("Write Dolphin CSV", {
        "event_count": num_events,
    })

def set_do4_directory(changed: bool) -> None:
    """Set directory to watch for do4 files"""
    _send_event("Browse D04 directory",{
        "directory_changed": changed,
    })

def cc_toggle(enable: bool) -> None:
    """Enable/disable Chromecast"""
    _send_event("Set Chromecast state",{
        "enable": enable,
    })

def _send_event(name: str, kvparams: Optional[Dict[str, Any]] = None) -> None:
    with sentry_sdk.start_span(op="analytics", description="Process analytics event"):
        if "user_id" not in _CONTEXT:
            return
        if kvparams is None:
            kvparams = {}
        analytics.track(_CONTEXT["user_id"], name, kvparams, context=_CONTEXT["context"])
        if analytics.write_key == "unknown": # dev environment
            print(f"Event: {name}")
            pprint(kvparams)

def _setup_context(screen_size: Tuple[int, int]) -> Dict[str, Any]:
    uname = platform.uname()
    # https://segment.com/docs/connections/spec/identify/#traits
    traits: Dict[str, Any] = {}
    if hasattr(socket,  "gethostname"):
        traits["name"] = socket.gethostname()

    # https://segment.com/docs/connections/spec/common/#context
    context: Dict[str, Any] = {
        "app": {
            "version": version.WAHOO_RESULTS_VERSION,
        },
        "locale": locale.getlocale()[0],
        "os": {
            "name": uname.system,
            "version": uname.version,
        },
        "screen": {
            "height": screen_size[1],
            "width": screen_size[0],
        },
        "traits": traits,
    }

    try:
        iphandler = ipinfo.getHandler(version.IPINFO_TOKEN)
        ipdetails = iphandler.getDetails()

        traits["address"] = {
            "city": ipdetails.city,
            "state": ipdetails.region,
            "country": ipdetails.country_name,
            "postalCode": ipdetails.postal,
        }
        context["ip"] = ipdetails.ip
        context["location"] = {
            "city": ipdetails.city,
            "region": ipdetails.region,
            "country": ipdetails.country_name,
            "latitude": ipdetails.latitude,
            "longitude": ipdetails.longitude,
        }
        context["timezone"] = ipdetails.timezone
    except requests.ConnectTimeout:
        pass

    print(context)
    return context
