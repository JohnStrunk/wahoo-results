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

'''
TKinter code to display a button that presents a colorpicker.
'''

import tkinter as tk
from tkinter import colorchooser  # type: ignore
from typing import Any

from config import WahooConfig

TkContainer = Any

class ColorButton(tk.Button):  # pylint: disable=too-many-ancestors
    '''Displays a button that allows choosing a color.'''
    def __init__(self, container: TkContainer, config: WahooConfig, color_option: str):
        super().__init__(container, bg=config.get_str(color_option), relief="solid",
                         padx=7, borderwidth=1, command=self._btn_cb)
        self._color_option = color_option
        self._config = config

    def _btn_cb(self) -> None:
        (_, rgb) = colorchooser.askcolor(self._config.get_str(self._color_option))
        if rgb is not None:
            self._config.set_str(self._color_option, rgb)
            self.configure(bg=self._config.get_str(self._color_option))
