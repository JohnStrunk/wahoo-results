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

"""Generate an image of the scoreboard from a RaceTimes object."""

from typing import Optional, Tuple

import sentry_sdk
from matplotlib import font_manager
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
from PIL.ImageEnhance import Brightness

from model import DQMode, Model
from raceinfo import Heat, NameMode, format_name, format_time


def waiting_screen(size: Tuple[int, int], model: Model) -> Image.Image:
    """Generate a "waiting" image to display on the scoreboard.

    :param size: The size of the image in pixels
    :param model: The application model state
    :returns: An image to display on the scoreboard
    """
    img = Image.new(mode="RGBA", size=size, color=model.color_bg.get())
    center = (int(size[0] * 0.5), int(size[1] * 0.8))
    normal = fontname_to_file(model.font_normal.get())
    font_size = 72
    fnt = ImageFont.truetype(normal, font_size)
    draw = ImageDraw.Draw(img)
    color = model.color_event.get()
    draw.text(center, "Waiting for results...", font=fnt, fill=color, anchor="ms")
    return img


class ScoreboardImage:
    """Generate a scoreboard image from a RaceTimes object."""

    _BORDER_FRACTION = 0.05  # Fraction of image left as a border around all sides
    _EVENT_SIZE = "E:MMM"
    _HEAT_SIZE = "H:MM"
    _img: Image.Image  # The rendered image
    _lanes: int  # The number of lanes to display
    _line_height: int  # Height of a line of text (baseline to baseline), in px
    _text_height: int  # Height of actual text, in px
    _normal_font: ImageFont.FreeTypeFont  # Font for normal text
    _time_font: ImageFont.FreeTypeFont  # Font for printing times

    def __init__(
        self,
        size: Tuple[int, int],
        race: Heat,
        model: Model,
        background: bool = True,
    ):
        """
        Generate a scoreboard image from a RaceTimes object.

        :param size: A tuple representing the size of the image in pixels
        :param race: The RaceTimes object containing the race result (and optionally the swimmer names/teams)
        :param model: The model state that contains the rendering preferences
        """
        with sentry_sdk.start_span(op="render_image", description="Render image"):
            self._race = race
            self._model = model
            # We save the lane count once because it's used multiple times, and we
            # want to ensure the value doesn't change while we're building the
            # scoreboard image
            self._lanes = model.num_lanes.get()
            bg_color = model.color_bg.get()
            if not background:
                bg_color = "#00000000"  # transparent
            self._img = Image.new(mode="RGBA", size=size, color=bg_color)
            if background:
                self._add_bg_image()
            self._load_fonts()
            self._draw_header()
            self._draw_lanes()

    @property
    def image(self) -> Image.Image:
        """The image of the scoreboard."""
        return self._img

    @property
    def size(self):
        """Get the size of the image."""
        return self._img.size

    def _add_bg_image(self) -> None:
        bg_image_filename = self._model.image_bg.get()
        if bg_image_filename == "":
            return  # bg image not defined
        try:
            bg_image = Image.open(bg_image_filename)
            # Ensure the size matches
            bg_image = bg_image.resize(self.size, Image.Resampling.BICUBIC)
            # Make sure the image modes match
            bg_image = bg_image.convert("RGBA")
            # Adjust the image brightness
            bg_image = Brightness(bg_image).enhance(
                float(self._model.brightness_bg.get()) / 100.0
            )
            # Overlay it, respecting the alpha channel
            self._img.alpha_composite(bg_image)
        except FileNotFoundError:
            return
        except UnidentifiedImageError:
            return
        except ValueError:
            return

    def _load_fonts(self) -> None:
        usable_height = self.size[1] * (1 - (2 * self._BORDER_FRACTION))
        lines = self._lanes
        lines += 1  # Event num + Header
        lines += 1  # Heat num + Event descr
        lines += 1  # Name, team, time header
        self._line_height = int(usable_height / lines)
        scaled_height = self._line_height / self._model.text_spacing.get()
        normal_f_file = fontname_to_file(self._model.font_normal.get())
        time_f_file = fontname_to_file(self._model.font_time.get())
        self._normal_font = ImageFont.truetype(normal_f_file, int(scaled_height))
        self._time_font = ImageFont.truetype(time_f_file, int(scaled_height))
        draw = ImageDraw.Draw(self._img)
        self._text_height = int(
            draw.textbbox((0, 0), self._EVENT_SIZE, self._normal_font)[3]
        )

    def _draw_header(self) -> None:
        draw = ImageDraw.Draw(self._img)
        edge_l = int(self.size[0] * self._BORDER_FRACTION)
        edge_r = int(self.size[0] * (1 - self._BORDER_FRACTION))
        width = edge_r - edge_l

        # Line1 - E: 999 Heading text
        draw.text(
            (edge_l, self._baseline(1)),
            f"E:{self._race.event}",
            font=self._time_font,
            anchor="ls",
            fill=self._model.color_event.get(),
        )
        hstart = edge_l + draw.textlength(self._EVENT_SIZE, self._normal_font)
        hwidth = width - hstart
        head_txt = self._model.title.get()
        while draw.textlength(head_txt, self._normal_font) > hwidth:
            head_txt = head_txt[:-1]
        draw.text(
            (edge_r, self._baseline(1)),
            head_txt,
            font=self._normal_font,
            anchor="rs",
            fill=self._model.color_title.get(),
        )

        # Line2 - H: 99 Event description
        draw.text(
            (edge_l, self._baseline(2)),
            f"H:{self._race.heat}",
            font=self._time_font,
            anchor="ls",
            fill=self._model.color_event.get(),
        )
        dstart = edge_l + draw.textlength(self._HEAT_SIZE, self._normal_font)
        dwidth = width - dstart
        desc_txt = self._race.description or ""
        while draw.textlength(desc_txt, self._normal_font) > dwidth:
            desc_txt = desc_txt[:-1]
        draw.text(
            (edge_r, self._baseline(2)),
            desc_txt,
            font=self._normal_font,
            anchor="rs",
            fill=self._model.color_event.get(),
        )

    def _draw_lanes(self) -> None:
        draw = ImageDraw.Draw(self._img)
        edge_l = int(self.size[0] * self._BORDER_FRACTION)
        edge_r = int(self.size[0] * (1 - self._BORDER_FRACTION))
        width = edge_r - edge_l
        time_width = int(draw.textlength("00:00.00", self._time_font) * 1.1)
        idx_width = draw.textlength("L", self._normal_font)
        pl_width = draw.textlength("MMM", self._normal_font)
        name_width = width - time_width - idx_width - pl_width
        dq_mode = DQMode(self._model.dq_mode.get())

        # Lane title
        baseline = self._baseline(3)
        title_color = self._model.color_event.get()
        draw.text(
            (edge_l, baseline),
            "L",
            font=self._normal_font,
            anchor="ls",
            fill=title_color,
        )
        draw.text(
            (edge_l + idx_width + pl_width, baseline),
            "Name",
            font=self._normal_font,
            anchor="ls",
            fill=title_color,
        )
        draw.text(
            (edge_r, baseline),
            "Time",
            font=self._normal_font,
            anchor="rs",
            fill=title_color,
        )

        # Lane data
        for i in range(1, self._lanes + 1):
            lane_num = i - 1 if self._race.numbering == "0-9" else i
            color = (
                self._model.color_odd.get() if i % 2 else self._model.color_even.get()
            )
            line_num = 3 + i
            # Lane
            draw.text(
                (edge_l + idx_width / 2, self._baseline(line_num)),
                f"{lane_num}",
                font=self._normal_font,
                anchor="ms",
                fill=color,
            )
            # Place
            pl_num = self._race.place(lane_num, dq_mode == DQMode.IGNORE)
            pl_color = color
            if pl_num == 1:
                pl_color = self._model.color_first.get()
            if pl_num == 2:  # noqa: PLR2004
                pl_color = self._model.color_second.get()
            if pl_num == 3:  # noqa: PLR2004
                pl_color = self._model.color_third.get()
            ptxt = format_place(pl_num)
            if self._race.lane(lane_num).is_dq and dq_mode == DQMode.DQ_TIME:
                ptxt = "DQ"
            draw.text(
                (edge_l + idx_width + pl_width / 2, self._baseline(line_num)),
                ptxt,
                font=self._normal_font,
                anchor="ms",
                fill=pl_color,
            )
            # Name
            raw_name = self._race.lane(lane_num).name or ""
            name_variants = format_name(NameMode.NONE, raw_name)
            while draw.textlength(name_variants[0], self._normal_font) > name_width:
                name_variants.pop(0)
            name = name_variants[0]
            draw.text(
                (edge_l + idx_width + pl_width, self._baseline(line_num)),
                f"{name}",
                font=self._normal_font,
                anchor="ls",
                fill=color,
            )
            # Time
            time_text = self._time_text(lane_num)
            if self._race.lane(lane_num).is_dq and dq_mode == DQMode.DQ_NOTIME:
                time_text = "DQ"
            draw.text(
                (edge_r, self._baseline(line_num)),
                time_text,
                font=self._time_font,
                anchor="rs",
                fill=color,
            )

    def _time_text(self, lane_num: int) -> str:
        lane = self._race.lane(lane_num)
        final_time = lane.final_time
        # Only print NS if someone was supposed to be there
        if lane.is_empty or lane.is_noshow:
            if lane.name is None or lane.name == "":
                return ""
            return "NS"
        if final_time is None:
            return "--:--.--"
        return format_time(final_time)

    def _baseline(self, line: int) -> int:
        """Return the y-coordinate for the baseline of the n-th line of text from the top."""
        return int(
            self._img.size[1] * self._BORDER_FRACTION  # skip top border
            + line * self._line_height  # move down to proper line
            - (self._line_height - self._text_height) / 2
        )  # up 1/2 the inter-line space


def fontname_to_file(name: str) -> str:
    """Convert a font name (Roboto) to its corresponding filename.

    :param name: The name of the font
    :returns: The filename of the font
    """
    properties = font_manager.FontProperties(family=name, weight="bold")
    filename = font_manager.findfont(properties)
    return filename


def format_place(place: Optional[int]) -> str:
    """
    Turn a numerical place into the printable string representation.

    >>> format_place(None)
    ''
    >>> format_place(0)
    ''
    >>> format_place(1)
    '1st'
    >>> format_place(2)
    '2nd'
    >>> format_place(3)
    '3rd'
    >>> format_place(6)
    '6th'
    """
    if place is None:
        return ""
    if place == 0:
        return ""
    if place == 1:
        return "1st"
    if place == 2:  # noqa: PLR2004
        return "2nd"
    if place == 3:  # noqa: PLR2004
        return "3rd"
    return f"{place}th"
