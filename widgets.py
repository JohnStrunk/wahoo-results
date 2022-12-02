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

import datetime
import os
from tkinter import VERTICAL, Button, Canvas, StringVar, TclError, Variable, \
    Widget, colorchooser, filedialog, ttk
from typing import Any, Dict, Generic, List, Literal, Optional, TypeVar

from PIL import ImageTk #type: ignore
import PIL.Image as PILImage

from config import WahooConfig
import imagecast

TkContainer = Any

_T = TypeVar('_T')

class GVar(Variable, Generic[_T]):
    '''
    Create a generic variable in the flavor of StringVar, IntVar, etc.

    - master: the master widget.
    - value: the initial value for the variable
    '''
    def __init__(self, value:_T, master=None):
        super().__init__(master=master, value=0)
        self._value = value

    def get(self) -> _T:
        """Returns the value of the variable."""
        _x = super().get()
        return self._value

    def set(self, value:_T) -> None:
        """Sets the variable to a new value."""
        self._value = value
        super().set(super().get() + 1)

class ImageVar(GVar[PILImage.Image]):
    """Value holder for PhotoImage variables."""

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

def swatch(width: int, height: int, color: str) -> ImageTk.PhotoImage:
    '''Generate a color swatch'''
    img = PILImage.new("RGBA", (width, height), color)
    return ImageTk.PhotoImage(img)

class ColorButton2(ttk.Button):  # pylint: disable=too-many-ancestors
    '''Displays a button that allows choosing a color.'''
    SWATCH_SIZE = 12
    def __init__(self, parent: Widget, color_var: StringVar):
        if color_var.get() == "":
            color_var.set("#000000")
        self._img = swatch(self.SWATCH_SIZE, self.SWATCH_SIZE, color_var.get())
        # super().__init__(parent, bg=color_var.get(), relief="solid",
        #                  padx=9, command=self._btn_cb)
        super().__init__(parent, command=self._btn_cb, image=self._img, padding=0)
        self._color_var = color_var
        def _on_change(_a, _b, _c):
            try:
                self._img = swatch(self.SWATCH_SIZE, self.SWATCH_SIZE, color_var.get())
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
    def __init__(self, parent: Widget, image_var: ImageVar):
        super().__init__(parent, width=self.WIDTH, height=self.HEIGHT)
        self._pimage: Optional[ImageTk.PhotoImage] = None
        self._image_var = image_var
        image_var.trace_add("write", lambda *_: self._set_image(self._image_var.get()))

    def _set_image(self, image: PILImage.Image) -> None:
        '''Set the preview image'''
        self.delete("all")
        scaled = image.resize((self.WIDTH, self.HEIGHT))
        # Note: In order for the image to display on the canvas, we need to
        # keep a reference to it, so it gets assigned to _pimage even though
        # it's not used anywhere else.
        self._pimage = ImageTk.PhotoImage(scaled)
        self.create_image(0, 0, image=self._pimage, anchor="nw")

StartListType = List[Dict[Literal['event', 'desc', 'heats'], str]]
class StartListVar(GVar[StartListType]):
    """Holds an ordered start list."""

class StartListTreeView(ttk.Frame):
    '''Widget to display a set of startlists'''
    def __init__(self, parent: Widget, startlist: StartListVar):
        super().__init__(parent)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.tview = ttk.Treeview(self, columns = ['event', 'desc', 'heats'])
        self.tview.grid(column=0, row=0, sticky="news")
        self.scroll = ttk.Scrollbar(self, orient=VERTICAL, command=self.tview.yview)
        self.scroll.grid(column=1, row=0, sticky="news")
        self.tview.configure(selectmode='none', show='headings', yscrollcommand=self.scroll.set)
        self.tview.column('event', anchor='w', minwidth=40, width=40)
        self.tview.heading('event', anchor='w', text='Event')
        self.tview.column('desc', anchor='w', minwidth=220, width=220)
        self.tview.heading('desc', anchor='w', text='Description')
        self.tview.column('heats', anchor='w', minwidth=40, width=40)
        self.tview.heading('heats', anchor='w', text='Heats')
        self.startlist = startlist
        startlist.trace_add("write", lambda *_: self._update_contents())

    def _update_contents(self):
        self.tview.delete(*self.tview.get_children())
        local_list = self.startlist.get()
        for entry in local_list:
            self.tview.insert('', 'end', id=entry['event'], values=[entry['event'],
            entry['desc'], entry['heats']])

class DirSelection(ttk.Frame):
    '''Directory selector widget'''
    def __init__(self, parent: Widget, directory: StringVar):
        super().__init__(parent)
        self.dir = directory
        self.columnconfigure(1, weight=1)
        self.btn = ttk.Button(self, text="Browse...", command=self._handle_browse)
        self.btn.grid(column=0, row=0, sticky="news")
        self.dir_label = StringVar()
        ttk.Label(self, textvariable=self.dir_label, relief="sunken").grid(column=1, row=0, sticky="news")
        self.dir.trace_add("write", lambda *_:
            self.dir_label.set(os.path.basename(self.dir.get())[-20:]))
        self.dir.set(self.dir.get())


    def _handle_browse(self) -> None:
        directory = filedialog.askdirectory(initialdir=self.dir.get())
        if len(directory) == 0:
            return
        directory = os.path.normpath(directory)
        self.dir.set(directory)

RaceResultType = List[Dict[Literal['meet', 'event', 'heat', 'time'], str]]
class RaceResultVar(GVar[RaceResultType]):
    """Holds an ordered list of race results."""

class RaceResultTreeView(ttk.Frame):
    '''Widget that displays a table of completed races'''
    def __init__(self, parent: Widget, racelist: RaceResultVar):
        super().__init__(parent)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.tview = ttk.Treeview(self, columns = ['meet', 'event', 'heat', 'time'])
        self.tview.grid(column=0, row=0, sticky="news")
        self.scroll = ttk.Scrollbar(self, orient=VERTICAL, command=self.tview.yview)
        self.scroll.grid(column=1, row=0, sticky="news")
        self.tview.configure(selectmode='none', show='headings', yscrollcommand=self.scroll.set)
        self.tview.column('meet', anchor='w', minwidth=50, width=50)
        self.tview.heading('meet', anchor='w', text='Meet')
        self.tview.column('event', anchor='w', minwidth=50, width=50)
        self.tview.heading('event', anchor='w', text='Event')
        self.tview.column('heat', anchor='w', minwidth=50, width=50)
        self.tview.heading('heat', anchor='w', text='Heat')
        self.tview.column('time', anchor='w', minwidth=140, width=140)
        self.tview.heading('time', anchor='w', text='Time')
        self.racelist = racelist
        racelist.trace_add("write", lambda *_: self._update_contents())

    def _update_contents(self):
        self.tview.delete(*self.tview.get_children())
        local_list = self.racelist.get()
        # Sort the list by date, descending
        # https://stackoverflow.com/a/39359270
        local_list.sort(key=lambda e: datetime.datetime.fromisoformat(e['time']), reverse=True)
        for entry in local_list:
            self.tview.insert('', 'end', id=entry['time'], values=[entry['meet'],
            entry['event'], entry['heat'], entry['time']])

class ChromecastStatusVar(GVar[List[imagecast.DeviceStatus]]):
    """Holds a list of Chromecast devices and whether they are enabled"""

class ChromcastSelector(ttk.Frame):
    '''Widget that allows enabling/disabling a set of Chromecast devices'''
    def __init__(self, parent: Widget, statusvar: ChromecastStatusVar) -> None:
        super().__init__(parent)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.tview = ttk.Treeview(self, columns = ['enabled', 'cc_name'])
        self.tview.grid(column=0, row=0, sticky="news")
        self.scroll = ttk.Scrollbar(self, orient=VERTICAL, command=self.tview.yview)
        self.scroll.grid(column=1, row=0, sticky="news")
        self.tview.configure(selectmode='none', show='headings', yscrollcommand=self.scroll.set)
        self.tview.column('enabled', anchor='center', width=30)
        self.tview.heading('enabled', anchor='center', text='Enabled')
        self.tview.column('cc_name', anchor='w', minwidth=100)
        self.tview.heading('cc_name', anchor='w', text='Chromecast')
        self.devstatus = statusvar
        self.devstatus.trace_add("write", lambda *_: self._update_contents())
        # Needs to be the ButtonRelease event because the Button event happens
        # before the focus is actually set/changed.
        self.tview.bind('<ButtonRelease-1>', self._item_clicked)
        self._update_contents()

    def _update_contents(self) -> None:
        self.tview.delete(*self.tview.get_children())
        local_list = self.devstatus.get()
        # Sort them by name for display
        local_list.sort(key=lambda d: (d['name']))
        for dev in local_list:
            txt_status = "Yes" if dev['enabled'] else "No"
            self.tview.insert('', 'end', id=str(dev['uuid']), values=[txt_status, dev['name']])

    def _item_clicked(self, _event) -> None:
        item = self.tview.focus()
        if len(item) == 0:
            return
        local_list = self.devstatus.get()
        for dev in local_list:
            if str(dev['uuid']) == item:
                dev['enabled'] = not dev['enabled']
        self.devstatus.set(local_list)
