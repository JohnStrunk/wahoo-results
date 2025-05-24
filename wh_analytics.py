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

"""Application usage analytics."""

import locale
import platform
import socket
import time
from pprint import pprint
from typing import Any

import ipinfo  # type: ignore
import ipinfo.exceptions  # type: ignore
import requests
import sentry_sdk
from segment import analytics  # type: ignore

import autotest
import version

_context: dict[str, Any] = {}


def application_start(
    analytics_enabled: bool, client_id: str, screen_size: tuple[int, int]
) -> None:
    """Event for application startup.

    :param model: Application model object
    :param screen_size: Screen size in pixels
    """
    analytics.write_key = version.SEGMENT_WRITE_KEY
    analytics.send = analytics_enabled
    global _context  # noqa: PLW0603
    _context = {
        "context": _setup_context(screen_size),
        "race_count": 0,
        "race_count_with_names": 0,
        "session_start": time.time(),
        "user_id": client_id,
    }

    if autotest.testing:  # Don't send analytics during testing
        return

    analytics.identify(  # type: ignore
        user_id=_context["user_id"],
        context=_context["context"],
        traits=_context["context"]["traits"],
    )
    _send_event("Scoreboard started")


def application_stop(  # noqa: PLR0913
    num_lanes: int,
    time_threshold: float,
    min_times: int,
    has_bg_image: bool,
    normal_font: str,
    time_font: str,
    dq_mode: str,
    result_format: str,
) -> None:
    """Event for application shutdown.

    :param model: Application model object
    """
    _send_event(
        "Scoreboard stopped",
        {
            "runtime": time.time() - _context["session_start"],
            "race_count": _context["race_count"],
            "race_count_with_names": _context["race_count_with_names"],
            "lane_count": num_lanes,
            "time_threshold": time_threshold,
            "min_times": min_times,
            "bg_image": has_bg_image,
            "normal_font": normal_font,
            "time_font": time_font,
            "dq_mode": dq_mode,
            "result_format": result_format,
        },
    )
    analytics.shutdown()


def results_received(has_names: bool, chromecasts: int) -> None:
    """Event for race results.

    :param has_names: True if names are included in the results
    :param chromecasts: Number of Chromecast devices currently enabled
    """
    _context["race_count"] += 1
    if has_names:
        _context["race_count_with_names"] += 1
    _send_event(
        "Results received", {"has_names": has_names, "chromecast_count": chromecasts}
    )


def image_sent(user_agent: str) -> None:
    """Event for image sent to Chromecast.

    :param user_agent: User agent string of the Chromecast
    """
    _send_event(
        "Image sent",
        {
            "user_agent": user_agent,
        },
    )


def documentation_link() -> None:
    """Follow link to online docs."""
    _send_event("Documentation click")


def update_link() -> None:
    """Follow link to download latest version."""
    _send_event("DownloadUpdate click")


def set_cts_directory(changed: bool) -> None:
    """Set CTS start list directory.

    :param changed: True if the directory was changed
    """
    _send_event(
        "Browse CTS directory",
        {
            "directory_changed": changed,
        },
    )


def wrote_dolphin_csv(num_events: int) -> None:
    """Dolphin CSV event list written.

    :param num_events: Number of events in the CSV file
    """
    _send_event(
        "Write Dolphin CSV",
        {
            "event_count": num_events,
        },
    )


def set_result_directory(changed: bool) -> None:
    """Set directory to watch for do4 files.

    :param changed: True if the directory was changed
    """
    _send_event(
        "Browse D04 directory",
        {
            "directory_changed": changed,
        },
    )


def cc_toggle(enable: bool) -> None:
    """Enable/disable a Chromecast.

    :param enable: True to enable, False to disable
    """
    _send_event(
        "Set Chromecast state",
        {
            "enable": enable,
        },
    )


def _send_event(name: str, kvparams: dict[str, Any] | None = None) -> None:
    with sentry_sdk.start_span(op="analytics", description="Process analytics event"):
        if "user_id" not in _context:
            return
        if autotest.testing:  # Don't send analytics during testing
            return
        if kvparams is None:
            kvparams = {}
        analytics.track(  # type: ignore
            _context["user_id"], name, kvparams, context=_context["context"]
        )
        if analytics.write_key == "unknown":  # type: ignore
            # dev environment
            print(f"Event: {name}")
            pprint(kvparams)


def _setup_context(screen_size: tuple[int, int]) -> dict[str, Any]:
    uname = platform.uname()
    # https://segment.com/docs/connections/spec/identify/#traits
    traits: dict[str, Any] = {}
    if hasattr(socket, "gethostname"):
        traits["name"] = socket.gethostname()

    # https://segment.com/docs/connections/spec/common/#context
    context: dict[str, Any] = {
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
        iphandler = ipinfo.getHandler(version.IPINFO_TOKEN)  # type: ignore
        ipdetails = iphandler.getDetails()  # type: ignore

        traits["address"] = {
            "city": ipdetails.city,  # type: ignore
            "state": ipdetails.region,  # type: ignore
            "country": ipdetails.country_name,  # type: ignore
            "postalCode": ipdetails.postal,  # type: ignore
        }
        context["ip"] = ipdetails.ip  # type: ignore
        context["location"] = {
            "city": ipdetails.city,  # type: ignore
            "region": ipdetails.region,  # type: ignore
            "country": ipdetails.country_name,  # type: ignore
            "latitude": ipdetails.latitude,  # type: ignore
            "longitude": ipdetails.longitude,  # type: ignore
        }
        context["timezone"] = ipdetails.timezone  # type: ignore
    except AttributeError:  # Tried to get a non-existant mapping from `ipdetails`
        pass
    except requests.HTTPError:  # General HTTP error
        pass
    except requests.JSONDecodeError:  # Invalid JSON returned
        pass
    except requests.Timeout:  # ConnectTimeout or ReadTimeout
        pass
    except ipinfo.exceptions.RequestQuotaExceededError:  # Over quota limit
        pass

    print(context)
    return context
