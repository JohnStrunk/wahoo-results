# Wahoo! Results - https://github.com/JohnStrunk/wahoo-results
# Copyright (C) 2025 - John D. Strunk
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

"""A window that shows the scoreboard contents."""

from tkinter import Tk, Toplevel

import PIL.Image as PILImage

import model
from tooltip import ToolTip
from widgets import ImageView


def make_sb_window(root: Tk, image_var: model.ImageVar) -> Toplevel:
    """Display a window containing the scoreboard contents.

    :param root: The main application window
    :return: The scoreboard window
    """
    dlg = Toplevel(root)

    dlg.title("Wahoo! Results - Scoreboard")

    dlg.protocol("WM_DELETE_WINDOW", dlg.destroy)  # intercept close button
    dlg.transient(root)  # dialog window is related to main

    # on double-click, toggle fullscreen
    def toggle_fullscreen(event) -> None:  # type: ignore
        """Toggle fullscreen mode."""
        is_fullscreen = dlg.attributes("-fullscreen")  # type: ignore
        dlg.attributes("-fullscreen", not is_fullscreen)  # type: ignore

    dlg.bind("<Double-Button-1>", toggle_fullscreen)  # type: ignore
    ToolTip(dlg, "Double-click to toggle fullscreen mode")

    img = ImageView(dlg, image_var=image_var)
    img.configure(background="black")  # set background color
    img.pack(expand=True, fill="both")  # fill the window with the image

    return dlg


def _main():
    """Test the scoreboard window."""
    root = Tk()
    # root.withdraw()  # hide the main window

    image = PILImage.new("RGB", (1280, 720), color="red")
    iv = model.ImageVar(image, root)

    sb_window = make_sb_window(root, iv)
    sb_window.geometry("1200x400")  # set initial size

    root.mainloop()


if __name__ == "__main__":
    _main()
