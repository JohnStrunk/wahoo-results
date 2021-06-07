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

"""Tests for results.py"""

import results

def test_parse_do4():
    """Ensure we can parse the do4 format correctly"""
    lines = """129;4;1;All
Lane1;0;0;0
Lane2;75.95;75.93;
Lane3;0;0;0
Lane4;73.33;73.32;
Lane5;0;0;0
Lane6;75.51;75.59;
Lane7;0;0;0
Lane8;0;0;0
Lane9;0;0;0
Lane10;0;0;0
F679E29E3D8A4CC4""".split("\n")

    res = results.Heat()
    res._parse_do4(lines)  # pylint: disable=protected-access
    assert res.event == "129"
    assert res.heat == 4
    assert res.num_expected_times() == 2
    assert len(res.lanes[0].times) == 0
    assert len(res.lanes[1].times) == 2
    assert res.lanes[0].is_empty()
    assert not res.lanes[3].is_empty()

def test_parse_do4_empty_event():
    """Handle empty event #s that happen when event list is empty/exhausted"""
    lines = """;1;1;All
Lane1;;353.00;
Lane2;344.68;344.76;
Lane3;330.82;330.61;
Lane4;354.49;354.46;
Lane5;341.58;341.58;
Lane6;352.50;352.67;
Lane7;0;0;0
Lane8;0;0;0
Lane9;0;0;0
Lane10;0;0;0
FDDEBE8AA47C716C""".split("\n")

    res = results.Heat()
    res._parse_do4(lines)  # pylint: disable=protected-access
    assert res.event == ""
    assert res.heat == 1
    assert res.num_expected_times() == 2
    assert len(res.lanes[0].times) == 1
    assert len(res.lanes[1].times) == 2
    assert res.lanes[6].is_empty()
    assert not res.lanes[3].is_empty()

def test_parse_scb():
    """Ensure we can parse the scb format correctly"""
    lines = """#18 BOYS 10&U 50 FLY
                    --                
                    --                
                    --                
PERSON, JUST A      --TEAM            
                    --                
BIGBIGBIGLY, NAMENAM--LONGLONGLONGLONG
                    --                
                    --                
                    --                
                    --                
                    --                
                    --                
                    --                
XXXXXXX, YYYYYY Z   --                
                    --                
AAAAA, B            --X               
                    --                
                    --                
                    --                
                    --                """.split("\n")
    assert len(lines) == 21
    res = results.Heat(event="18", heat=1)
    res._parse_scb(lines)  # pylint: disable=protected-access
    assert res.event_desc == "BOYS 10&U 50 FLY"
    assert res.lanes[3].name == "PERSON, JUST A"
    assert res.lanes[3].team == "TEAM"
    assert res.lanes[5].name == "BIGBIGBIGLY, NAMENAM"
    assert res.lanes[5].team == "LONGLONGLONGLONG"
    assert not res.lanes[3].is_empty()
    assert res.lanes[4].is_empty()

    res = results.Heat(event="18", heat=2)
    res._parse_scb(lines)  # pylint: disable=protected-access
    assert res.event_desc == "BOYS 10&U 50 FLY"
    assert res.lanes[3].name == "XXXXXXX, YYYYYY Z"
    assert res.lanes[3].team == ""
    assert res.lanes[5].name == "AAAAA, B"
    assert res.lanes[5].team == "X"
