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

from tkinter import *
from tkinter import colorchooser
from typing import Any, Optional
import tkinter.ttk as ttk

from PIL import ImageTk #type: ignore
import PIL.Image as PILImage

from config import WahooConfig

TkContainer = Any

class ImageVar(Variable):
    """Value holder for PhotoImage variables."""
    _default = PILImage.Image()

    def __init__(self, master=None, value=None, name=None):
        """Construct a PhotoImage variable.

        MASTER can be given as master widget.
        VALUE is an optional value
        NAME is an optional Tcl name (defaults to PY_VARnum).

        If NAME matches an existing variable and VALUE is omitted
        then the existing value is retained.
        """
        super().__init__(master, value, name)

    def get(self):
        """Return value of variable as Image."""
        value = self._tk.globalgetvar(self._name)
        if isinstance(value, Image.Image):
            return value
        raise TypeError("Value is not an Image")

class ColorButton(Button):  # pylint: disable=too-many-ancestors
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

def swatch(width: int, height: int, color: str) -> PhotoImage:
    img = PILImage.new("RGBA", (width, height), color)
    return ImageTk.PhotoImage(img)

class ColorButton2(ttk.Button):  # pylint: disable=too-many-ancestors
    '''Displays a button that allows choosing a color.'''
    def __init__(self, parent: Widget, color_var: StringVar):
        if color_var.get() == "":
            color_var.set("#000000")
        self._img = swatch(12, 12, color_var.get())
        # super().__init__(parent, bg=color_var.get(), relief="solid",
        #                  padx=9, command=self._btn_cb)
        super().__init__(parent, command=self._btn_cb, image=self._img, padding=0)
        self._color_var = color_var
        def _on_change(_a, _b, _c):
            try:
                self._img = swatch(10, 10, color_var.get())
                self.configure(image=self._img)
            except TclError: # configuring an invalid color throws
                pass
        self._color_var.trace_add("write", _on_change)

    def _btn_cb(self) -> None:
        (_, rgb) = colorchooser.askcolor(self._color_var.get())
        if rgb is not None:
            self._color_var.set(rgb)

class Preview(Canvas):
    """A widget that displays a scoreboard preview image"""
    WIDTH = 320
    HEIGHT = 180
    _pimage: Optional[ImageTk.PhotoImage]
    def __init__(self, parent: Widget, image_var: ImageVar):
        super().__init__(parent, width=self.WIDTH, height=self.HEIGHT)
        self._pimage = None
        self._image_var = image_var
        image_var.trace_add("write", lambda _a, _b, _c: self.set_image(self._image_var.get()))

    def set_image(self, image: PILImage.Image) -> None:
        '''Set the preview image'''
        self.delete("all")
        scaled = image.resize((self.WIDTH, self.HEIGHT))
        # Note: In order for the image to display on the canvas, we need to
        # keep a reference to it, so it gets assigned to _pimage even though
        # it's not used anywhere else.
        self._pimage = ImageTk.PhotoImage(scaled)
        self.create_image(0, 0, image=self._pimage, anchor="nw")
