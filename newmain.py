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

'''Wahoo Results!'''

import datetime
from tkinter import Tk, messagebox
from typing import List
import uuid
from PIL import Image

import main_window
import imagecast
from scoreboard import ScoreboardImage
from template import get_template
import widgets

def main():
    '''Main program'''
    root = Tk()

    model = main_window.Model()
    model.load("wahoo-results.ini")
    main_window.View(root, model)

    # Exit menu exits app
    def exit_fn():
        try:
            model.save("wahoo-results.ini")
        except PermissionError as err:
            messagebox.showerror(title="Error saving configuration",
                message=f'Unable to write configuration file "{err.filename}". {err.strerror}',
                detail="Please ensure the working directory is writable.")
        root.destroy()

    model.menu_exit.add(exit_fn)

    slist: widgets.StartListType = [
        {'event': '102', 'desc': 'Girls 13&O 200 Free', 'heats': '12'},
        {'event': '101', 'desc': 'Boys 13&O 200 Free', 'heats': '32'},
        {'event': '110', 'desc': 'Boys 13&O 100 Free', 'heats': '2'},
    ]
    model.startlist_contents.set(slist)

    raceres: widgets.RaceResultType = [
        {'meet': '10', 'event': '102', 'heat': '12',
        'time': str(datetime.datetime(2022, 2, 3, 12, 37, 23))},
        {'meet': '9', 'event': '102', 'heat': '12',
        'time': str(datetime.datetime(2023, 2, 3, 12, 37, 23))},
    ]
    model.results_contents.set(raceres)

    cc_devs: List[imagecast.DeviceStatus] = [
        {'uuid': uuid.uuid4(), 'name': 'Living room', 'enabled': False},
        {'uuid': uuid.uuid4(), 'name': 'Computer room', 'enabled': True},
        {'uuid': uuid.uuid4(), 'name': 'Main scoreboard', 'enabled': False},
    ]
    model.cc_status.set(cc_devs)
    model.scoreboard_preview.set(Image.new(mode="RGBA", size=(1280, 720),
                    color="brown"))

    # Any time the "appearance settings" are changed, we should regenerate the
    # scoreboard preview image
    def update_preview(_a, _b, _c) -> None:
        preview = ScoreboardImage((1280, 720), get_template(), model)
        model.appearance_preview.set(preview.image)
    for element in [
        model.main_text,
        model.time_text,
        model.text_spacing,
        model.heading,
        model.bg_image,
        model.color_heading,
        model.color_event,
        model.color_even,
        model.color_odd,
        model.color_first,
        model.color_second,
        model.color_third,
        model.color_bg,
        model.num_lanes,
    ]: element.trace_add("write", update_preview)
    update_preview(None, None, None)

    root.mainloop()

if __name__ == "__main__":
    main()
