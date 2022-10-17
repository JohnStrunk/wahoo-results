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

'''Layouts to simplify arranging GUI elements'''

from enum import auto, Enum, unique
from tkinter import ttk, Widget
from typing import Any

@unique
class Orientation(Enum):
    """Allowed orientations for Linear layouts"""
    HORIZONTAL = auto()
    VERTICAL = auto()

class Linear(ttk.Frame):  # pylint: disable=too-many-ancestors
    """
    Creates an invisible Frame used for generating GUI layouts in the style of
    Android's LinearLayout class.
    See: https://developer.android.com/reference/android/widget/Linear
    """
    def __init__(self, parent: Widget, orientation: Orientation) -> None:
        self._orientation = orientation
        super().__init__(parent)
        self._index = 0
        if self._orientation == Orientation.HORIZONTAL:
            self.rowconfigure(0, weight=1)
        else:
            self.columnconfigure(0, weight=1)

    def append(self, child, **kwargs) -> None:
        """Add a child element into the layout at the next available position."""
        if self._orientation == Orientation.HORIZONTAL:
            kwargs["column"] = self._index
            kwargs["row"] = 0
        else:
            kwargs["column"] = 0
            kwargs["row"] = self._index
        child.grid(**kwargs)
        self._index += 1
