# Wahoo! Results - https://github.com/JohnStrunk/wahoo-results
# Copyright (C) 2020 - John D. Strunk
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

'''Config parsing'''

import configparser

class WahooConfig:
    '''Get/Set program options'''

    # Name of the configuration file
    _CONFIG_FILE = "wahoo-results.ini"
    # Name of the section we use in the ini file
    _INI_HEADING = "wahoo-results"
    # Configuration defaults if not present in the config file
    _CONFIG_DEFAULTS = {_INI_HEADING: {
        "dolphin_dir": "c:\\CTSDolphin",
        "start_list_dir": "c:\\swmeets8",
        "num_lanes": "10",      # Number of lanes on the board
        "color_bg": "black",    # Window background
        "color_fg": "white",    # Main text color
        "place_1": "#00FFFF",   # 1st place marker
        "place_2": "#FF0000",   # 2nd place marker
        "place_3": "#FFFF00",   # 3rd place marker
        "image_bg": "",         # background image
        "image_bright": "0.3",  # bg image brightness (0-1)
        "normal_font": "Helvetica",  # Main font
        "time_font": "Helvetica",    # Font for times
        "font_scale": 0.67,     # scale of font relative to line height
    }}

    def __init__(self):
        self._config = configparser.ConfigParser()
        self._config.read_dict(self._CONFIG_DEFAULTS)
        self._config.read(self._CONFIG_FILE)

    def save(self) -> None:
        '''Save the (updated) configuration to the ini file'''
        with open(self._CONFIG_FILE, 'w') as configfile:
            self._config.write(configfile)

    def get_str(self, name: str) -> str:
        '''Get a string option'''
        return self._config.get(self._INI_HEADING, name)

    def set_str(self, name: str, value: str) -> str:
        '''Set a string option'''
        self._config.set(self._INI_HEADING, name, value)
        return self.get_str(name)

    def get_float(self, name: str) -> float:
        '''Get a float option'''
        return self._config.getfloat(self._INI_HEADING, name)

    def set_float(self, name: str, value: float) -> float:
        '''Set a float option'''
        self._config.set(self._INI_HEADING, name, str(value))
        return self.get_float(name)

    def get_int(self, name: str) -> int:
        '''Get an integer option'''
        return self._config.getint(self._INI_HEADING, name)

    def set_int(self, name: str, value: int) -> int:
        '''Set an integer option'''
        self._config.set(self._INI_HEADING, name, str(value))
        return self.get_int(name)
