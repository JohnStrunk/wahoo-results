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

'''Analytics for Wahoo! Results'''

import concurrent.futures
#import json
from typing import Any, Dict
import requests

from config import WahooConfig
from version import WAHOO_RESULTS_VERSION

# GA4
# https://developers.google.com/analytics/devguides/collection/protocol/ga4
MEASUREMENT_ID = 'G-PQNGGSM3WF'
API_SECRET = '5lVU9z1wQFSuSYNrGihfQA'
ANALYTICS_URL = 'https://www.google-analytics.com/mp/collect'
#ANALYTICS_URL = 'https://www.google-analytics.com/debug/mp/collect'

# pylint: disable=global-statement,invalid-name
_config: WahooConfig
_executor: concurrent.futures.ThreadPoolExecutor
_screen_size: str

def send_application_start(config: WahooConfig, screen_size: str) -> None:
    '''Event: Application start'''
    global _config
    global _executor
    global _screen_size
    _config = config
    _executor = concurrent.futures.ThreadPoolExecutor()
    _screen_size = screen_size
    send_event("application_start")

def send_application_stop() -> None:
    '''Event: Application stop'''
    send_event("application_stop")
    _executor.shutdown()

def screen_view(screen_name: str, kvparams: Dict[str, Any] = None) -> None:
    '''Send a screen_view event'''
    params = {"screen_name": screen_name}
    if kvparams is not None:
        params.update(kvparams)
    send_event("screenview", params) # screen_view is reserved

def send_event(event_name: str, kvparams: Dict[str, Any] = None) -> None:
    '''Send an arbitrary analytics event.'''
    if not _config.get_bool('analytics'):  # analytics are disabled
        return
    if kvparams is None:
        kvparams = {}

    params = {
        "measurement_id": MEASUREMENT_ID,
        "api_secret": API_SECRET,
    }
    data = {
        "client_id": _config.get_str('client_id'),
        "user_properties": {
            "version": {"value": WAHOO_RESULTS_VERSION},
            "screen_size": {"value": _screen_size},
        },
        "events": [
            {
                "name": event_name,
                "params": kvparams,
            }
        ]
    }
    _executor.submit(_post, url=ANALYTICS_URL, params=params, json=data, timeout=5)

def _post(**args) -> None:
    requests.post(**args)
    #print(req.request.url)
    #print(json.dumps(json.loads(req.request.body), indent=2))
    #print(json.dumps(req.json(), indent=2))
