# Wahoo! Results - https://github.com/JohnStrunk/wahoo-results
# Copyright (C) 2021 - John D. Strunk
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
Generates an image of the scoreboard from a Result object.
'''

import tkinter as tk
from typing import Tuple
from PIL import Image, ImageDraw, ImageFont, ImageTk, UnidentifiedImageError #type: ignore
from PIL.ImageEnhance import Brightness #type: ignore

from config import WahooConfig
from results import Heat

def _format_time(time_seconds: float) -> str:
    """
    >>> _format_time(1.2)
    '01.20'
    >>> _format_time(9.87)
    '09.87'
    >>> _format_time(50)
    '50.00'
    >>> _format_time(120.0)
    '2:00.00'
    """
    minutes = int(time_seconds//60)
    seconds = time_seconds - minutes*60.0
    if minutes == 0:
        return f"{seconds:05.2f}"
    return f"{minutes}:{seconds:05.2f}"

def _format_place(place: int) -> str:
    """
    >>> _format_place(1)
    '1st'
    >>> _format_place(6)
    '6th'
    """
    if place == 0:
        return ""
    if place == 1:
        return "1st"
    if place == 2:
        return "2nd"
    if place == 3:
        return "3rd"
    return f"{place}th"


class ScoreboardImage:
    '''
    Converts a result (Heat) to an image of the specified dimensions.

    Parameters:
        heat: The result to display
        size: A 2-tuple containing the size of the resulting image
        config: The program configuration
    '''
    # Fraction of the image that should be empty border
    _BORDER_FRACTION = 0.05
    # Extra gap between the header and lane table
    _HEADER_GAP = 0.05

    _heat: Heat
    _i: Image.Image
    _config: WahooConfig

    def __init__(self, heat: Heat, size: Tuple[int, int],
                 config: WahooConfig):
        super().__init__()
        self._heat = heat
        self._config = config
        self._i = Image.new(mode="RGBA", size=size,
                            color=self._config.get_str("color_bg"))
        self._add_background()
        self._make_fonts()
        self._draw_header()
        self._draw_lanes()

    @property
    def image(self) -> Image.Image:
        '''Get the image representing the scoreboard'''
        return self._i

    @property
    def size(self):
        '''Get the size of the image'''
        return self._i.size

    def _add_background(self):
        bg_file = self._config.get_str("image_bg")
        if bg_file == "":
            return  # Nothing to do (no image)

        # Scale the image
        try:
            bg_img = Image.open(bg_file)
        except FileNotFoundError:
            return
        except UnidentifiedImageError:
            return
        mode = self._config.get_str("image_scale")
        alg = Image.BICUBIC
        if mode == "stretch":
            bg_img = bg_img.resize(self.size, alg)
        elif mode == "fit":
            factor = min(self.size[0]/bg_img.size[0], self.size[1]/bg_img.size[1])
            bg_img = bg_img.resize((int(bg_img.size[0]*factor),
                                    int(bg_img.size[1]*factor)), alg)
        elif mode == "cover":
            factor = max(self.size[0]/bg_img.size[0], self.size[1]/bg_img.size[1])
            bg_img = bg_img.resize((int(bg_img.size[0]*factor), int(bg_img.size[1]*factor)), alg)

        # Generate the crop bounding box such that the image is in the center
        # and the size matches the size of the main image
        left = (bg_img.size[0] - self.size[0]) // 2
        right = bg_img.size[0] - left
        top = (bg_img.size[1] - self.size[1]) // 2
        bottom = bg_img.size[1] - top
        bbox = (left, top, right, bottom)
        bg_img = bg_img.crop(bbox)

        # Adjust brightness and overlay it on the main image
        bg_img = Brightness(bg_img).enhance(self._config.get_float("image_bright"))
        self._i.alpha_composite(bg_img)

    def _make_fonts(self) -> None:
        normal = self._config.get_str("normal_font")
        times = self._config.get_str("time_font")
        lanes = self._config.get_int("num_lanes")
        line_height = int(self.size[1] *
                          (1 - 2 * self._BORDER_FRACTION - self._HEADER_GAP) /
                          (lanes + 2))
        draw = ImageDraw.Draw(self._i)
        font_size = [1, 500]
        while (font_size[1] - font_size[0]) > 1:
            size = (font_size[0] + font_size[1]) // 2
            fnt = ImageFont.truetype(normal, size)
            height = draw.textsize("M", fnt)[1]
            if height > line_height:
                font_size[1] = size
            else:
                font_size[0] = size
        self._line_height = line_height
        scale = self._config.get_float("font_scale")
        self._normalfont = ImageFont.truetype(normal, int(size * scale))
        self._timefont = ImageFont.truetype(times, int(size * scale))

    def _draw_header(self) -> None:
        head_color = self._config.get_str("color_ehd")
        sizing_string = "E: MMM / H: MM"
        draw = ImageDraw.Draw(self._i)
        edge_l = int(self.size[0] * self._BORDER_FRACTION)
        edge_r = int(self.size[0] * (1 - self._BORDER_FRACTION))
        width = edge_r - edge_l
        txt_size = draw.textsize(sizing_string, self._normalfont)
        desc_width = width - txt_size[0]
        baseline = self.size[1] * self._BORDER_FRACTION + self._line_height
        draw.text((edge_l, baseline), f"E: {self._heat.event} / H: {self._heat.heat}",
               font=self._normalfont, anchor="ls", fill=head_color)
        descr = self._heat.event_desc
        while draw.textsize(descr, self._normalfont)[0] > desc_width:
            descr = descr[:-1]
        draw.text((edge_r, baseline), descr, font=self._normalfont, anchor="rs", fill=head_color)

    def _draw_lanes(self) -> None: # pylint: disable=too-many-locals
        num_lanes = self._config.get_int("num_lanes")
        fg_color = self._config.get_str("color_fg")
        draw = ImageDraw.Draw(self._i)
        edge_l = int(self.size[0] * self._BORDER_FRACTION)
        edge_r = int(self.size[0] * (1 - self._BORDER_FRACTION))
        width = edge_r - edge_l
        time_width = int(draw.textsize("00:00.00", self._timefont)[0] * 1.2)
        idx_width = draw.textsize("Lane", self._normalfont)[0]
        pl_width = draw.textsize("MMM", self._normalfont)[0]
        name_width = width - time_width - idx_width - pl_width
        baseline = int(self.size[0] * (self._BORDER_FRACTION + self._HEADER_GAP) \
            + self._line_height)
        draw.text((edge_l, baseline), "Lane", font=self._normalfont, anchor="ls", fill=fg_color)
        draw.text((edge_l + idx_width + pl_width, baseline), "Name",
               font=self._normalfont, anchor="ls", fill=fg_color)
        draw.text((edge_r, baseline), "Time", font=self._normalfont, anchor="rs", fill=fg_color)
        line_y = baseline + self._line_height/4
        draw.line([(edge_l, line_y), (edge_r, line_y)], fill=fg_color,
               width=int(0.06*self._line_height), joint="curve")
        for i in range(0, num_lanes):
            y_coord = baseline + (i+1) * self._line_height
            # Lane
            draw.text((edge_l + idx_width/2, y_coord),
                   f"{i+1}", font=self._normalfont, anchor="ms", fill=fg_color)
            # Place
            pl_num = self._heat.place(i)
            pl_color = fg_color
            if pl_num == 1:
                pl_color = self._config.get_str("place_1")
            if pl_num == 2:
                pl_color = self._config.get_str("place_2")
            if pl_num == 3:
                pl_color = self._config.get_str("place_3")
            ptxt = _format_place(self._heat.place(i))
            draw.text((edge_l + idx_width + pl_width/2, y_coord),
                   ptxt, font=self._normalfont, anchor="ms", fill=pl_color)
            # Name
            name = self._heat.lanes[i].name
            while draw.textsize(name, self._normalfont)[0] > name_width:
                name = name[:-1]
            draw.text((edge_l + idx_width + pl_width, y_coord),
                   f"{name}", font=self._normalfont, anchor="ls", fill=fg_color)
            # Time
            time_txt = _format_time(float(self._heat.lanes[i].final_time()))
            if not self._heat.lanes[i].times_are_valid() \
               and self._config.get_bool("inhibit_inconsistent"):
                time_txt = "--:--.--"
            if self._heat.lanes[i].final_time() == 0.0:
                time_txt = ""
            draw.text((edge_r, y_coord),
                   time_txt, font=self._timefont, anchor="rs", fill=fg_color)


###########################################################################
def _mockup(config: WahooConfig) -> Heat:
    heat = Heat(allow_inconsistent = not config.get_bool("inhibit_inconsistent"))
     #pylint: disable=protected-access
    heat._parse_do4("""129;1;1;All
Lane1;123.00;122.00;0
Lane2;60;60;0
Lane3;75.51;75.59;
Lane4;13.33;13.32;
Lane5;0;0;0
Lane6;75.95;75.93;
Lane7;615.01;615.15;0
Lane8;87.65;87.88;0
Lane9;300.00;300.10;0
Lane10;121.02;120.80;0
F679E29E3D8A4CC4""".split("\n"))
    heat._parse_scb("""#129 GIRLS 13 & OVER 200 FLY
SWIMMER, FIRST Z    --ABC             
SWIMMER, ANOTHER    --                
REALLYREALLYLONGNAME--                
PERSON, JUST A      --TEAM            
SWIM, NO            --                
BIGBIGBIGLY, NAMENAM--LONGLONGLONGLONG
GO, INEDA           --FAST            
SWIM, SLOW          --                
NAMES, BORING       --                
IDEAS, OUT O        --                """.split("\n"))
    return heat

def _main():
    '''Display a scoreboard mockup'''
    root = tk.Tk()
    # Chromecast images are always 1280x720, so we design the image to look
    # good at those dimensions.
    size = (1280, 720)
    canvas = tk.Canvas(root, width=size[0], height=size[1])
    canvas.configure(bg="black", borderwidth=0)
    canvas.pack()
    root.update()

    # Create the SB image
    config = WahooConfig()
    heat = _mockup(config)
    image = ScoreboardImage(heat, size, config).image
    image.save("file.png")

    pimage = ImageTk.PhotoImage(image)
    canvas.create_image(canvas.winfo_width()//2, canvas.winfo_height()//2,
                        image=pimage, anchor="center")

    root.mainloop()

if __name__ == '__main__':
    _main()
