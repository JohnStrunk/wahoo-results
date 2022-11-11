import datetime
from tkinter import Tk, ttk
import tkinter
import platform
from PIL import Image

import main_window
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
    root.mainloop()

if __name__ == "__main__":
    main()
