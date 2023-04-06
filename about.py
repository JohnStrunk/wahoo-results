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

'''
Display an "about" dialog
'''

import textwrap
from tkinter import Text, Tk, Toplevel, font, ttk

from version import WAHOO_RESULTS_VERSION


def about(root: Tk) -> None:
    '''Displays a modal dialog containing the application "about" info'''

    dlg = Toplevel(root)
    dlg.resizable(False, False) # don't allow resizing

    def dismiss():
        dlg.grab_release()
        dlg.destroy()

    text = Text(dlg, state="disabled", wrap="none")
    _set_contents(text)
    text.grid(column=0, row=0, sticky="news")
    ttk.Button(dlg, text="Ok", command=dismiss).grid(column=0, row=1)

    dlg.title("About - Wahoo! Results")
    dlg.configure(padx=8, pady=8)

    dlg.protocol("WM_DELETE_WINDOW", dismiss) # intercept close button
    dlg.transient(root)   # dialog window is related to main
    dlg.wait_visibility() # can't grab until window appears, so we wait
    dlg.grab_set()        # ensure all input goes to our window

    geo = dlg.geometry()
    # parse the geometry string of the form "WxH+X+Y" to get the width and height as integers
    width, height = [int(x) for x in geo.split('+')[0].split('x')]
    # center the dialog on the screen
    left = root.winfo_screenwidth() // 2 - width // 2
    top = root.winfo_screenheight() // 2 - height // 2
    dlg.geometry(f'+{left}+{top}')

    dlg.wait_window()     # block until window is destroyed

def _set_contents(txt: Text) -> None:
    contents = textwrap.dedent(f'''\
        Wahoo! Results
        Copyright (c) 2022 - John Strunk

        This is free software, licensed under the
        GNU Affero General Public License v3 or later

        https://github.com/JohnStrunk/wahoo-results

        Version: {WAHOO_RESULTS_VERSION}
    ''')

    txtfont = font.nametofont('TkTextFont')
    txtsize = txtfont.actual()["size"]

    # Add contents and set default style
    lines = contents.split('\n')
    height = len(lines)
    width = 0
    for line in lines:
        width = max(width, len(line))
    txt.configure(state="normal", background=txt.master["background"], relief="flat",
    width=width, height=height)
    txt.insert("1.0", contents, ("all"))
    txt.tag_configure("all", foreground="black",  font=f"TktextFont {txtsize}", justify="center")

    # Set the style for the application title text line
    txt.tag_add('title', '1.0', '2.0')
    txt.tag_configure("title", font=f"TkTextFont {txtsize} bold underline")

    txt.configure(state="disabled")
    txt.see("1.0")

if __name__ == "__main__":
    about(Tk())
