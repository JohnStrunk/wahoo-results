# Wahoo! Results - https://github.com/JohnStrunk/wahoo-results
# Copyright (C) 2022 - John D. Strunk
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

"""Monitor the startlist directory"""

from typing import Callable

import watchdog.events  # type: ignore

CallbackFn = Callable[[], None]
CreatedCallbackFn = Callable[[str], None]


class SCBWatcher(watchdog.events.PatternMatchingEventHandler):
    """Monitors a directory for changes to CTS Startlist files"""

    def __init__(self, callback: CallbackFn):
        super().__init__(patterns=["*.scb"], ignore_directories=True)
        self._callback = callback

    def on_any_event(self, event: watchdog.events.FileSystemEvent):
        self._callback()


class DO4Watcher(watchdog.events.PatternMatchingEventHandler):
    """Monitors a directory for new .do4 race result files"""

    def __init__(self, callback: CreatedCallbackFn):
        super().__init__(patterns=["*.do4"], ignore_directories=True)
        self._callback = callback

    def on_created(self, event: watchdog.events.FileCreatedEvent):
        self._callback(event.src_path)
