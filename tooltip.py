"""
From: https://stackoverflow.com/questions/3221956/how-do-i-display-tooltips-in-tkinter

tk_ToolTip_class101.py
gives a Tkinter widget a tooltip as the mouse is above the widget
tested with Python27 and Python34  by  vegaseat  09sep2014
www.daniweb.com/programming/softip_winare-development/code/484591/a-tooltip-class-for-tkinter

Modified to include a delay time by Victor Zaccardo, 25mar16
"""

import tkinter as tk

class ToolTip: # pylint: disable=too-few-public-methods
    """
    create a tooltip for a given widget
    """
    def __init__(self, widget, text='widget info'):
        self.waittime = 500     #miliseconds
        self.wraplength = 180   #pixels
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self._enter)
        self.widget.bind("<Leave>", self._leave)
        self.widget.bind("<ButtonPress>", self._leave)
        self._id = None
        self._tip_win = None

    def _enter(self, _=None):
        self._schedule()

    def _leave(self, _=None):
        self._unschedule()
        self._hidetip()

    def _schedule(self):
        self._unschedule()
        self._id = self.widget.after(self.waittime, self._showtip)

    def _unschedule(self):
        my_id = self._id
        self._id = None
        if my_id:
            self.widget.after_cancel(my_id)

    def _showtip(self, _=None):
        # pylint: disable=invalid-name
        x = y = 0
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # creates a toplevel window
        self._tip_win = tk.Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self._tip_win.wm_overrideredirect(True)
        self._tip_win.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self._tip_win, text=self.text, justify='left',
                         background="#ffffff", relief='solid', borderwidth=1,
                         wraplength = self.wraplength)
        label.pack(ipadx=1)

    def _hidetip(self):
        tip_win = self._tip_win
        self._tip_win= None
        if tip_win:
            tip_win.destroy()

# testing ...
if __name__ == '__main__':
    root = tk.Tk()
    btn1 = tk.Button(root, text="button 1")
    btn1.pack(padx=10, pady=5)
    button1_ttp = ToolTip(btn1, \
   'Neque porro quisquam est qui dolorem ipsum quia dolor sit amet, '
   'consectetur, adipisci velit. Neque porro quisquam est qui dolorem ipsum '
   'quia dolor sit amet, consectetur, adipisci velit. Neque porro quisquam '
   'est qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit.')

    btn2 = tk.Button(root, text="button 2")
    btn2.pack(padx=10, pady=5)
    button2_ttp = ToolTip(btn2, \
    "First thing's first, I'm the realest. Drop this and let the whole world "
    "feel it. And I'm still in the Murda Bizness. I could hold you down, like "
    "I'm givin' lessons in  physics. You should want a bad Vic like this.")
    root.mainloop()
