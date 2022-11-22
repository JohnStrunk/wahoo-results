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

import datetime
from tkinter import Tk, ttk
import tkinter
import platform
from PIL import Image
from typing import List
import uuid

import main_window
import imagecast
import widgets

def main():
    root = Tk()

    vm = main_window.ViewModel()
    main_window.View(root, vm)

    # Exit menu exits app
    vm.on_menu_exit = lambda: root.destroy()
    vm.appearance_preview.set(Image.new(mode="RGBA", size=(1280, 720),
                    color="green"))

    def cb(name: str, _a, _b):
        v = root.getvar(name)
        print(f'Value: {v}')

    vm.main_text.trace_add("write", cb)

    root.update()

    sl: widgets.StartListType = [
        {'event': '102', 'desc': 'Girls 13&O 200 Free', 'heats': '12'},
        {'event': '101', 'desc': 'Boys 13&O 200 Free', 'heats': '32'},
        {'event': '110', 'desc': 'Boys 13&O 100 Free', 'heats': '2'},
    ]
    vm.startlist_contents.set(sl)

    rr: widgets.RaceResultType = [
        {'meet': '10', 'event': '102', 'heat': '12', 'time': str(datetime.datetime(2022, 2, 3, 12, 37, 23))},
        {'meet': '9', 'event': '102', 'heat': '12', 'time': str(datetime.datetime(2023, 2, 3, 12, 37, 23))},
    ]
    vm.results_contents.set(rr)

    cc: List[imagecast.DeviceStatus] = [
        {'uuid': uuid.uuid4(), 'name': 'Living room', 'enabled': False},
        {'uuid': uuid.uuid4(), 'name': 'Computer room', 'enabled': True},
        {'uuid': uuid.uuid4(), 'name': 'Main scoreboard', 'enabled': False},
    ]
    vm.cc_status.set(cc)
    vm.scoreboard_preview.set(Image.new(mode="RGBA", size=(1280, 720),
                    color="brown"))

    root.mainloop()

if __name__ == "__main__":
    main()
