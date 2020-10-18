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

'''A canvas text item w/ bounded width'''

import tkinter as tk
import tkinter.font as tkfont

class BoundedText:
    '''
    Wrapper for a Canvas text item that truncates the text at the specified
    width instead of wrapping.
    '''
    _full_text: str
    _max_width: int
    _canvas: tk.Canvas
    _id: int

    def __init__(self, canvas: tk.Canvas, xpos: int, ypos: int, **kwargs):
        self._canvas = canvas
        self._font = kwargs.setdefault("font", tkfont.Font())
        self._full_text = kwargs.setdefault("text", "")
        self._max_width = kwargs.get("width", 0)
        kwargs["width"] = 0
        self._id = canvas.create_text(xpos, ypos, kwargs)
        self.update()

    @property
    def id(self): # pylint: disable=invalid-name
        '''Get the object id of the text item'''
        return self._id

    @property
    def text(self):
        '''Update the widget text'''
        return self._full_text
    @text.setter
    def text(self, new_text):
        self._full_text = new_text
        self.update()

    @property
    def width(self):
        '''Update the maximum width of the widget'''
        return self._max_width
    @width.setter
    def width(self, new_width):
        self._max_width = new_width
        self.update()

    def move_to(self, xpos, ypos):
        '''Change the anchor point of the text item'''
        self._canvas.coords(self._id, xpos, ypos)

    @property
    def font(self):
        '''Change the font of the text item'''
        return self._font

    @font.setter
    def font(self, font):
        self._font = font
        self._canvas.itemconfigure(self._id, font=font)
        self.update()

    def configure(self, **kwargs):
        '''Configure an attribute of the text item'''
        self._canvas.itemconfigure(self._id, kwargs)
        self.update()

    def update(self):
        '''Update the widget's size'''
        self._canvas.itemconfigure(self._id, text=self._full_text)
        if self._max_width == 0:
            return
        chars = len(self._full_text)
        text = self._full_text
        for i in range(chars, 0, -1):
            if self._font.measure(text) > self._max_width:
                text = text[0:i]
            else:
                break
        self._canvas.itemconfigure(self._id, text=text)
