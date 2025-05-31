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

"""TKinter code to display various UI widgets."""

import copy
import os
from datetime import datetime
from tkinter import (
    VERTICAL,
    Canvas,
    Misc,
    StringVar,
    TclError,
    colorchooser,
    filedialog,
    ttk,
)
from typing import Any

import PIL.Image as PILImage
from PIL import ImageTk

from model import (
    ChromecastStatusVar,
    ImageVar,
    RaceResultListVar,
    RaceResultVar,
    StartListVar,
)
from raceinfo import Time, format_time

TkContainer = Any


def swatch(width: int, height: int, color: str) -> ImageTk.PhotoImage:
    """Generate a color swatch.

    :param width: Width of the swatch
    :param height: Height of the swatch
    :param color: Color for the swatch
    """
    img = PILImage.new("RGBA", (width, height), color)
    return ImageTk.PhotoImage(img)


class ColorButton2(ttk.Button):
    """Displays a button that allows choosing a color."""

    SWATCH_SIZE = 12

    def __init__(self, parent: Misc, color_var: StringVar):
        """Create a Button that allows choosing a color.

        :param parent: Parent widget
        :param color_var: StringVar to hold the associated color value
        """
        if color_var.get() == "":
            color_var.set("#000000")
        self._img = swatch(self.SWATCH_SIZE, self.SWATCH_SIZE, color_var.get())
        super().__init__(parent, command=self._btn_cb, image=self._img, padding=0)
        self._color_var = color_var

        def _on_change(var: str, idx: str, op: str) -> None:
            try:
                self._img = swatch(self.SWATCH_SIZE, self.SWATCH_SIZE, color_var.get())
                self.configure(image=self._img)
            except TclError:  # configuring an invalid color throws
                pass

        self._color_var.trace_add("write", _on_change)

    def _btn_cb(self) -> None:
        (_, rgb) = colorchooser.askcolor(self._color_var.get())
        if rgb is not None:
            self._color_var.set(rgb)


class ImageView(Canvas):
    """A widget that displays an image."""

    def __init__(self, parent: Misc, image_var: ImageVar):
        """Create a preview widget for a scoreboard image.

        :param parent: Parent widget
        :param image_var: Variable to hold the associated image
        """
        super().__init__(parent)
        self._img: ImageTk.PhotoImage | None = None
        self._image_var = image_var
        # Watch for changes to the image and redraw the canvas
        self._trace_name = image_var.trace_add(
            "write", lambda var, idx, op: self._draw()
        )
        # Configure event is triggered when the widget is resized
        self.bind("<Configure>", lambda event: self._draw())
        self.bind("<Destroy>", self._on_destroy)  # type:ignore

    def _on_destroy(self, event):  # type:ignore
        if event.widget is not self:  # type:ignore
            return
        self._image_var.trace_remove("write", self._trace_name)

    def _draw(self) -> None:
        image = self._image_var.get()
        # Calculate scale to fit image within canvas, preserving aspect ratio
        canvas_width = self.winfo_width()
        canvas_height = self.winfo_height()
        img_width, img_height = image.size
        scale = min(canvas_width / img_width, canvas_height / img_height)
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        if new_width <= 0 or new_height <= 0:
            return
        scaled = image.resize((new_width, new_height), PILImage.Resampling.BICUBIC)  # type:ignore

        # Note: In order for the image to display on the canvas, we need to
        # keep a reference to it, so it gets assigned to _img even though
        # it's not used anywhere else.
        self._img = ImageTk.PhotoImage(scaled)
        self.delete("all")
        self.create_image(  # type:ignore
            canvas_width // 2,
            canvas_height // 2,
            image=self._img,
            anchor="center",
        )


class StartListTreeView(ttk.Frame):
    """Widget to display a set of startlists."""

    def __init__(self, parent: Misc, startlist: StartListVar):
        """Widget to display a set of startlists.

        :param parent: Parent widget
        :param startlist: Variable containing startlists to display
        """
        super().__init__(parent)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.tview = ttk.Treeview(self, columns=["event", "desc", "heats"])
        self.tview.grid(column=0, row=0, sticky="news")
        self.scroll = ttk.Scrollbar(self, orient=VERTICAL, command=self.tview.yview)  # type: ignore
        self.scroll.grid(column=1, row=0, sticky="news")
        self.tview.configure(
            selectmode="none", show="headings", yscrollcommand=self.scroll.set
        )
        self.tview.column("event", anchor="w", minwidth=40, width=40)
        self.tview.heading("event", anchor="w", text="Event")
        self.tview.column("desc", anchor="w", minwidth=220, width=220)
        self.tview.heading("desc", anchor="w", text="Description")
        self.tview.column("heats", anchor="w", minwidth=40, width=40)
        self.tview.heading("heats", anchor="w", text="Heats")
        self.startlist = startlist
        startlist.trace_add("write", lambda var, idx, op: self._update_contents())

    def _update_contents(self):
        self.tview.delete(*self.tview.get_children())
        program = copy.deepcopy(self.startlist.get())
        local_list = [
            program[event]
            for event in sorted(program.keys(), key=lambda ev: program[ev][0])
        ]
        for entry in local_list:
            self.tview.insert(
                "",
                "end",
                id=entry[0].event or "",  # Not sure about empty string here
                values=[entry[0].event, entry[0].description, str(len(entry))],
            )


class DirSelection(ttk.Frame):
    """Directory selector widget."""

    def __init__(self, parent: Misc, directory: StringVar):
        """Directory selector widget.

        :param parent: Parent widget
        :param directory: Variable containing the selected directory (path)
        """
        super().__init__(parent)
        self.dir = directory
        self.columnconfigure(1, weight=1)
        self.btn = ttk.Button(self, text="Browse...", command=self._handle_browse)
        self.btn.grid(column=0, row=0, sticky="news")
        self.dir_label = StringVar()
        ttk.Label(self, textvariable=self.dir_label, relief="sunken").grid(
            column=1, row=0, sticky="news"
        )
        self.dir.trace_add(
            "write",
            lambda var, idx, op: self.dir_label.set(
                os.path.basename(self.dir.get())[-20:]
            ),
        )
        self.dir.set(self.dir.get())

    def _handle_browse(self) -> None:
        directory = filedialog.askdirectory(initialdir=self.dir.get())
        if len(directory) == 0:
            return
        directory = os.path.normpath(directory)
        self.dir.set(directory)


class RaceResultTreeView(ttk.Frame):
    """Widget that displays a table of completed races."""

    def __init__(self, parent: Misc, racelist: RaceResultListVar):
        """Widget that displays a table of completed races.

        :param parent: Parent widget
        :param racelist: Variable containing a list of race results
        """
        super().__init__(parent)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.tview = ttk.Treeview(self, columns=["meet", "event", "heat", "time"])
        self.tview.grid(column=0, row=0, sticky="news")
        self.scroll = ttk.Scrollbar(self, orient=VERTICAL, command=self.tview.yview)  # type: ignore
        self.scroll.grid(column=1, row=0, sticky="news")
        self.tview.configure(
            selectmode="none", show="headings", yscrollcommand=self.scroll.set
        )
        self.tview.column("meet", anchor="w", minwidth=50, width=50)
        self.tview.heading("meet", anchor="w", text="Meet")
        self.tview.column("event", anchor="w", minwidth=50, width=50)
        self.tview.heading("event", anchor="w", text="Event")
        self.tview.column("heat", anchor="w", minwidth=50, width=50)
        self.tview.heading("heat", anchor="w", text="Heat")
        self.tview.column("time", anchor="w", minwidth=140, width=140)
        self.tview.heading("time", anchor="w", text="Time")
        self.racelist = racelist
        racelist.trace_add("write", lambda var, idx, op: self._update_contents())

    def _update_contents(self):
        self.tview.delete(*self.tview.get_children())
        local_list = self.racelist.get()
        now = datetime.now()
        # Sort the list by date, descending
        # https://stackoverflow.com/a/39359270
        local_list.sort(key=lambda e: e.time_recorded or now, reverse=True)
        for entry in local_list:
            timetext = (
                entry.time_recorded.strftime("%Y-%m-%d %H:%M:%S")
                if entry.time_recorded
                else ""
            )
            id = str(entry.meet_id) + str(entry.event) + str(entry.heat)
            self.tview.insert(
                "",
                "end",
                id=id,
                values=[str(entry.meet_id), entry.event, entry.heat, timetext],
            )


class ChromcastSelector(ttk.Frame):
    """Widget that allows enabling/disabling a set of Chromecast devices."""

    def __init__(self, parent: Misc, statusvar: ChromecastStatusVar) -> None:
        """Widget that allows enabling/disabling a set of Chromecast devices.

        :param parent: Parent widget
        :param statusvar: Variable containing Chromecast device status
        """
        super().__init__(parent)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.tview = ttk.Treeview(self, columns=["enabled", "cc_name"])
        self.tview.grid(column=0, row=0, sticky="news")
        self.scroll = ttk.Scrollbar(self, orient=VERTICAL, command=self.tview.yview)  # type: ignore
        self.scroll.grid(column=1, row=0, sticky="news")
        self.tview.configure(
            selectmode="none", show="headings", yscrollcommand=self.scroll.set
        )
        self.tview.column("enabled", anchor="center", width=30)
        self.tview.heading("enabled", anchor="center", text="Enabled")
        self.tview.column("cc_name", anchor="w", minwidth=100)
        self.tview.heading("cc_name", anchor="w", text="Chromecast name")
        self.devstatus = statusvar
        self.devstatus.trace_add("write", lambda var, idx, op: self._update_contents())
        # Needs to be the ButtonRelease event because the Button event happens
        # before the focus is actually set/changed.
        self.tview.bind("<ButtonRelease-1>", self._item_clicked)
        self._update_contents()

    def _update_contents(self) -> None:
        self.tview.delete(*self.tview.get_children())
        local_list = self.devstatus.get()
        # Sort them by name for display
        local_list.sort(key=lambda d: (d.name))
        for dev in local_list:
            txt_status = "Yes" if dev.enabled else "No"
            self.tview.insert(
                "", "end", id=str(dev.uuid), values=[txt_status, dev.name]
            )

    def _item_clicked(self, _event: Any) -> None:
        item = self.tview.focus()
        if len(item) == 0:
            return
        local_list = self.devstatus.get()
        for dev in local_list:
            if str(dev.uuid) == item:
                dev.enabled = not dev.enabled
        self.devstatus.set(local_list)


class RaceResultView(ttk.LabelFrame):
    """Widget that displays a RaceResult."""

    def __init__(self, parent: Misc, resultvar: RaceResultVar) -> None:
        """Widget that displays a RaceResult.

        :param parent: Parent widget
        :param resultvar: Variable containing the result of a race
        """
        super().__init__(parent, text="Latest result")
        self._resultvar = resultvar
        self._resultvar.trace_add("write", lambda var, idx, op: self._update())
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.tview = ttk.Treeview(
            self,
            columns=["lane", "pad", "t1", "t2", "t3", "final"],
            selectmode="none",
            show="headings",
        )
        self.tview.grid(column=0, row=0, sticky="news")
        # Column configuration
        time_width = 55
        self.tview.heading("lane", anchor="e", text="Lane")
        self.tview.column("lane", anchor="e", width=35)
        self.tview.heading("pad", anchor="e", text="Pad")
        self.tview.column("pad", anchor="e", width=time_width)
        self.tview.heading("t1", anchor="e", text="Time #1")
        self.tview.column("t1", anchor="e", width=time_width)
        self.tview.heading("t2", anchor="e", text="Time #2")
        self.tview.column("t2", anchor="e", width=time_width)
        self.tview.heading("t3", anchor="e", text="Time #3")
        self.tview.column("t3", anchor="e", width=time_width)
        self.tview.heading("final", anchor="e", text="Final")
        self.tview.column("final", anchor="e", width=time_width)
        self._update()

    def _update(self) -> None:
        self.tview.delete(*self.tview.get_children())
        result = self._resultvar.get()
        for l_index in range(1, 11):
            if result is None:
                self.tview.insert(
                    "",
                    "end",
                    id=str(l_index),
                    values=[str(l_index), "", "", "", "", ""],
                )
            else:
                lane = l_index - 1 if result.numbering == "0-9" else l_index
                padtime = format_time(result.lane(lane).primary)
                rawtimes: list[Time | None] = [None, None, None]
                backups = result.lane(lane).backups
                if backups is not None:
                    for i, b in enumerate(backups):
                        rawtimes[i] = b
                timestr = [format_time(t) if t is not None else "" for t in rawtimes]
                final = result.lane(lane).final_time
                if final is not None:
                    finalstr = format_time(final)
                elif result.lane(lane).is_noshow:
                    finalstr = "NS"
                elif result.lane(lane).is_dq:
                    finalstr = "DQ"
                else:
                    finalstr = "????"
                self.tview.insert(
                    "",
                    "end",
                    id=str(lane),
                    values=[
                        str(lane),
                        padtime,
                        timestr[0],
                        timestr[1],
                        timestr[2],
                        finalstr,
                    ],
                )
