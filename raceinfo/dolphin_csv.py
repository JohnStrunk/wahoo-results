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

"""Colorado Dolphin timing system.

https://coloradotime.com/products/dolphin-wireless-stopwatch-swim-timing
"""

import io
import os
import re
from datetime import datetime

from .time import Heat, parse_time, truncate_hundredths
from .timingsystem import TimingSystem


class DolphinCSV(TimingSystem):
    """Colorado Dolphin Wireless Stopwatch - CSV format."""

    def read(self, filename: str) -> Heat:  # noqa: D102
        with open(filename, "r", encoding="cp1252") as file:
            heat = self.decode(file)
        matcher = re.match(
            r"^(\d+)_Event_(\d*)_Heat_(\d+)_Race_(\d+)_(\d+)_(\d+)_(\d+)_(\d+)_(\d+)\.csv$",
            os.path.basename(filename),
        )
        if matcher is not None:
            heat.meet_id = str(matcher.group(1))
            heat.event = str(matcher.group(2))
            heat.heat = int(matcher.group(3))
            heat.race = int(matcher.group(4))
            mon = int(matcher.group(5))
            day = int(matcher.group(6))
            year = int(matcher.group(7))
            hour = int(matcher.group(8))
            minute = int(matcher.group(9))
            heat.time_recorded = datetime(
                year=year, month=mon, day=day, hour=hour, minute=minute
            )
        return heat

    def decode(self, stream: io.TextIOBase) -> Heat:  # noqa: D102
        _ = stream.readline()  # Skip the header line
        lines = stream.readlines()
        # Note that the file seems to have an extra blank line at the end, so we
        # allow 10 or 11 lines (after the header).
        if len(lines) < 10 or len(lines) > 11:  # noqa: PLR2004
            raise ValueError("Too few lines in file")
        heat = Heat()
        heat.numbering = "0-9" if lines[0].startswith("0") else "1-10"
        for line in lines:
            if len(line) < 2:  # noqa: PLR2004
                continue  # Skip blank lines
            fields = line.split(",")
            if len(fields) != 7:  # noqa: PLR2004
                raise ValueError("Invalid number of fields in line")
            lane_num = int(fields[0])
            timer_a = parse_time(fields[1])
            timer_b = parse_time(fields[2])
            timer_c = parse_time(fields[3])
            heat.lane(lane_num).backups = [timer_a, timer_b, timer_c]
            heat.lane(lane_num).is_empty = fields[5].lower().startswith("true")
            heat.lane(lane_num).is_dq = fields[6].lower().startswith("true")
        return heat

    def write(self, filename: str, heat: Heat) -> None:  # noqa: D102
        super().write(filename, heat)

    def encode(self, heat: Heat) -> str:  # noqa: D102
        lines = ["Lane,Timer A,Timer B,Timer C,Final,Empty,DQ"]
        lane_offset = 0 if heat.numbering == "0-9" else 1
        for lane in range(10):
            lane_num = lane + lane_offset
            splits = heat.lane(lane_num).splits
            backups = heat.lane(lane_num).backups
            if backups is not None:  # Prefer backups for the times
                times = backups
            elif splits is not None:  # Try splits if no backups
                times = splits[-1]
            else:
                times = [None, None, None]
            # Ensure we have three times
            while len(times) < 3:  # noqa: PLR2004
                times.append(None)
            primary = heat.lane(lane_num).primary
            if primary is not None:
                final = primary
            else:
                valid = [t for t in times if t is not None]
                if len(valid) == 0:
                    final = None
                elif len(valid) == 1:
                    final = valid[0]
                elif len(valid) == 2:  # noqa: PLR2004
                    final = truncate_hundredths((valid[0] + valid[1]) / 2)
                else:
                    final = sorted(valid)[1]
            empty = "True" if heat.lane(lane_num).is_empty else "False"
            dq = "True" if heat.lane(lane_num).is_dq else "False"
            line = f"{lane_num},{times[0] or ''},{times[1] or ''},{times[2] or ''},{final or ''},{empty},{dq}"
            lines.append(line)
        return "\n".join(lines)

    def filename(self, heat: Heat) -> str | None:  # noqa: D102
        if (
            heat.meet_id is None
            or heat.heat is None
            or heat.race is None
            or heat.time_recorded is None
        ):
            return None
        event = heat.event if heat.event is not None else ""
        return f"{int(heat.meet_id):03}_Event_{event}_Heat_{heat.heat}_Race_{heat.race}_{heat.time_recorded.month}_{heat.time_recorded.day}_{heat.time_recorded.year}_{heat.time_recorded.hour}_{heat.time_recorded.minute}.csv"

    @property
    def patterns(self) -> list[str]:
        """A list of file name patterns for this timing system."""
        return ["*Event*Heat*Race*.csv"]
