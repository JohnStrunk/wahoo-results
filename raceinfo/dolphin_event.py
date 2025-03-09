# Wahoo! Results - https://github.com/JohnStrunk/wahoo-results
# Copyright (C) 2024 - John D. Strunk
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

"""Interface to Dolphin CSV event files."""

from .eventprocessor import EventProcessor, FullProgram


class DolphinEvent(EventProcessor):
    """Write a meet program as a CSV file for import into the Dolphin timing system."""

    def write(self, path: str, program: FullProgram) -> None:  # noqa: D102
        csv = self._prog_to_csv(program)
        with open(path, "w", encoding="cp1252") as file:
            file.writelines(csv)

    def _prog_to_csv(self, program: FullProgram) -> list[str]:
        csv: list[str] = []
        # Sort the events, using the sort order of the Heat object
        events = sorted(program.keys(), key=lambda event: program[event][0])
        for event in events:
            description = program[event][0].description or ""
            heats = len(program[event])
            # TODO: Add support for splits based on distance
            csv.append(f"{event},{description},{heats},1,A\n")
        return csv
