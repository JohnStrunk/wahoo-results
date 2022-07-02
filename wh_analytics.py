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
import socket
import time
from typing import Any, Dict, Tuple

import analytics  # type: ignore
import ipinfo  # type: ignore

from config import WahooConfig
import version

_CONTEXT: Dict[str, Any]

def application_start(config: WahooConfig, screen_size: Tuple[int, int],
    exe_environ: str) -> None:
    """Event for application startup"""
    analytics.write_key = version.SEGMENT_WRITE_KEY
    analytics.send = config.get_bool("analytics")
    global _CONTEXT  # pylint: disable=global-statement
    _CONTEXT = {
        "context": _setup_context(screen_size, exe_environ),
        "race_count": 0,
        "race_count_with_names": 0,
        "session_start": time.time(),
        "user_id": config.get_str("client_id"),
    }

    analytics.identify(
        user_id = _CONTEXT["user_id"],
        context = _CONTEXT["context"],
        traits = _CONTEXT["context"]["traits"],
    )
    _send_event("Scoreboard started")

def application_stop(config: WahooConfig) -> None:
    """Event for application shutdown"""
    _send_event("Scoreboard stopped", {
        "runtime": time.time() - _CONTEXT["session_start"],
        "race_count": _CONTEXT["race_count"],
        "race_count_with_names": _CONTEXT["race_count_with_names"],
        "lane_count": config.get_int("num_lanes"),
        "inhibit": config.get_bool("inhibit_inconsistent"),
        "bg_image": config.get_str("image_bg") != "",
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

def clear_btn() -> None:
    """Clear scoreboard event"""
    _send_event("Clear")

def test_btn() -> None:
    """Test scoreboard event"""
    _send_event("Test")

def manual_result() -> None:
    """Publish a manually loaded result event"""
    _send_event("Manual result")

def documentation_link() -> None:
    """Follow link to docs event"""
    _send_event("Documentation click")

def update_link() -> None:
    """Follow link to dl latest version event"""
    _send_event("DownloadUpdate click")

def _send_event(name: str, kvparams: Dict[str, Any] = None) -> None:
    if kvparams is None:
        kvparams = {}
    analytics.track(_CONTEXT["user_id"], name, kvparams, context=_CONTEXT["context"])
    if analytics.write_key == "unknown": # dev environment
        print(f"Event: {name}")

def _setup_context(screen_size: Tuple[int, int], exe_environ: str) -> Dict[str, Any]:
    uname = platform.uname()
    iphandler = ipinfo.getHandler(version.IPINFO_TOKEN)
    ipdetails = iphandler.getDetails()

    # https://segment.com/docs/connections/spec/identify/#traits
    traits = {
        "address": {
            "city": ipdetails.city,
            "state": ipdetails.region,
            "country": ipdetails.country_name,
            "postalCode": ipdetails.postal
         },
    }
    if hasattr(socket,  "gethostname"):
        traits["name"] = socket.gethostname()

    # https://segment.com/docs/connections/spec/common/#context
    return {
        "app": {
            "version": version.WAHOO_RESULTS_VERSION,
            "environment": exe_environ,
        },
        "ip": ipdetails.ip,
        "locale": locale.getdefaultlocale()[0],
        "location": {
            "city": ipdetails.city,
            "region": ipdetails.region,
            "country": ipdetails.country_name,
            "latitude": ipdetails.latitude,
            "longitude": ipdetails.longitude,
        },
        "os": {
            "name": uname.system,
            "version": uname.version,
        },
        "screen": {
            "height": screen_size[1],
            "width": screen_size[0],
        },
        "timezone": ipdetails.timezone,
        "traits": traits,
    }
