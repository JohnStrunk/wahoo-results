from tkinter import Tk, ttk
import tkinter
import platform
from PIL import Image

import main_window

def main():
    root = Tk()

    # if platform.system() == "Windows":
    #     s=ttk.Style()
    #     #s.theme_use("winnative")
    #     #s.theme_use("vista")

    vm = main_window.ViewModel()
    main_window.View(root, vm)

    # Exit menu exits app
    vm.on_menu_exit = lambda: root.destroy()
    vm.appearance_preview.set(Image.new(mode="RGBA", size=(1280, 720),
                    color="black"))

    def cb(name: str, _a, _b):
        v = root.getvar(name)
        print(f'Value: {v}')

    vm.main_text.trace_add("write", cb)

    root.mainloop()

if __name__ == "__main__":
    main()
