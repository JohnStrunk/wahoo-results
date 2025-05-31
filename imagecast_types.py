# Wahoo! Results - https://github.com/JohnStrunk/wahoo-results
# Copyright (C) 2025 - John D. Strunk
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

"""Abstract interactions with Chromecast devices."""

from dataclasses import dataclass
from uuid import UUID

# Resolution of images for the Chromecast
IMAGE_SIZE = (1280, 720)


@dataclass
class DeviceStatus:
    """The status of a Chromecast device."""

    uuid: UUID  # UUID for the device
    name: str  # Friendly name for the device
    enabled: bool  # Whether the device is enabled
