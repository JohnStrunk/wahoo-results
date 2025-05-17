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

"""Colorado SCB file format tests."""

import io
import textwrap
from datetime import datetime

import pytest

from .colorado_scb import ColoradoSCB

_now = datetime.now()
_meet_seven = "007"
_parse = ColoradoSCB()._parse_scb  # type: ignore


class TestColoradoSCB:
    """Tests for the Colorado SCB file format."""

    @pytest.fixture()
    def scb_invalid_header(self):
        """SCB data with an invalid header (event, descr) line."""
        return io.StringIO(
            textwrap.dedent(
                """\
                INVALID HEADER
                                    --                
                                    --                
                                    --                
                PERSON, JUST A      --TEAM            
                                    --                
                BIGBIGBIGLY, NAMENAM--LONGLONGLONGLONG
                                    --                
                                    --                
                                    --                
                                    --                """
            )
        )

    @pytest.fixture()
    def scb_wrong_num_lines(self):
        """SCB data with an invalid number of lines (not multiple of 10 + 1)."""
        return io.StringIO(
            textwrap.dedent(
                """\
                #10 BOYS 8&U 50 FLY
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
                                    --                """
            )
        )

    @pytest.fixture()
    def scb_invalid_line(self):
        """SCB data with an invalid line."""
        return io.StringIO(
            textwrap.dedent(
                """\
                #10 BOYS 8&U 50 FLY
                                    --                
                INVALID LINE
                                    --                
                PERSON, JUST A      --TEAM            
                                    --                
                BIGBIGBIGLY, NAMENAM--LONGLONGLONGLONG
                                    --                
                                    --                
                                    --                
                                    --                """
            )
        )

    @pytest.fixture()
    def scb_zero_heats(self):
        """SCB data with no heats."""
        return io.StringIO(
            textwrap.dedent(
                """\
                #10 BOYS 8&U 50 FLY"""
            )
        )

    @pytest.fixture()
    def scb_one_heat(self):
        """SCB data with one heat."""
        return io.StringIO(
            textwrap.dedent(
                """\
                #10 BOYS 8&U 50 FLY
                                    --                
                                    --                
                                    --                
                PERSON, JUST A      --TEAM            
                                    --                
                BIGBIGBIGLY, NAMENAM--LONGLONGLONGLONG
                                    --                
                                    --                
                                    --                
                                    --                """
            )
        )

    @pytest.fixture()
    def scb_two_heats(self):
        """SCB data with two heats."""
        return io.StringIO(
            textwrap.dedent(
                """\
                #18 BOYS 10&U 50 FLY
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
                                    --                """
            )
        )

    @pytest.fixture()
    def scb_six_heats(self):
        """SCB data with six heats."""
        return io.StringIO(
            textwrap.dedent(
                """\
                #34 GIRLS 15&O 50 BACK
                                    --                
                                    --                
                SANTIAGO, LINDSEY 0 --BLUE            
                BROWN, LORRAINE 0   --BLUE            
                HARRISON, JOSEPHINE --GREEN           
                DRAKE, MELISSA 0    --RED             
                                    --                
                                    --                
                                    --                
                                    --                
                LOWE, DOREEN 1      --GREEN           
                BRYAN, MARIA 1      --GREEN           
                PATTON, MOLLY 0     --GREEN           
                SUTTON, SARA 0      --GREEN           
                PARKS, SONYA 0      --RED             
                HANSEN, JANE 1      --RED             
                WADE, CHARLOTTE 0   --GREEN           
                WELCH, ALBERTA 0    --GREEN           
                                    --                
                                    --                
                FLOYD, PHYLLIS 0    --BLUE            
                HENRY, SOPHIA 0     --RED             
                PEREZ, EDNA 0       --RED             
                GREER, JENNA 0      --RED             
                ALVAREZ, FREDA 0    --RED             
                WASHINGTON, LYNDA 1 --GREEN           
                MILLS, JASMINE 0    --GREEN           
                DELGADO, BESSIE 0   --RED             
                                    --                
                                    --                
                COLEMAN, RENEE 0    --BLUE            
                TURNER, TAMARA 0    --RED             
                THORNTON, NAOMI 1   --GREEN           
                INGRAM, LESLIE 1    --BLUE            
                LARSON, EDNA 0      --GREEN           
                INGRAM, LOLA 1      --RED             
                CARPENTER, ERMA 0   --BLUE            
                HARRINGTON, STACY 0 --BLUE            
                                    --                
                                    --                
                ESTRADA, KRISTINA 0 --GREEN           
                ZIMMERMAN, LYDIA 0  --BLUE            
                HARVEY, SILVIA 0    --BLUE            
                PATTERSON, PATTI 1  --BLUE            
                DAVIS, MYRTLE 1     --RED             
                CRAIG, KRYSTAL 0    --RED             
                WILKINS, VICKIE 0   --RED             
                SINGLETON, LORENE 1 --RED             
                                    --                
                                    --                
                COLE, CYNTHIA 1     --BLUE            
                HARDY, LAVERNE 0    --RED             
                KELLER, LATOYA 1    --GREEN           
                WATERS, ROBIN 0     --GREEN           
                PADILLA, ESSIE 0    --BLUE            
                SCHMIDT, KATHY 0    --GREEN           
                WASHINGTON, TRACEY 1--RED             
                MCDANIEL, SUZANNE 1 --GREEN           
                                    --                
                                    --                """
            )
        )

    def test_can_read_event(self, scb_two_heats: io.StringIO):
        """Make sure we can read the event number and description."""
        heatlist = _parse(scb_two_heats)
        assert len(heatlist) == 2  # noqa: PLR2004
        for heat in heatlist:
            assert heat.event == "18"
            assert heat.description == "BOYS 10&U 50 FLY"
        assert heatlist[0].heat == 1
        assert heatlist[1].heat == 2  # noqa: PLR2004

    def test_invalid_header_throws(self, scb_invalid_header: io.StringIO):
        """Make sure we throw an error if the header is invalid."""
        with pytest.raises(ValueError):
            _parse(scb_invalid_header)

    def test_wrong_num_lines_throws(self, scb_wrong_num_lines: io.StringIO):
        """Make sure we throw an error if the number of lines in the file is wrong."""
        with pytest.raises(ValueError):
            _parse(scb_wrong_num_lines)

    def test_invalid_line_throws(self, scb_invalid_line: io.StringIO):
        """Make sure we throw an error if a line is invalid."""
        with pytest.raises(ValueError):
            _parse(scb_invalid_line)

    def test_can_read_one_heat(self, scb_one_heat: io.StringIO):
        """Make sure we can read a single heat."""
        heatlist = _parse(scb_one_heat)
        assert len(heatlist) == 1
        assert heatlist[0].event == "10"
        assert heatlist[0].description == "BOYS 8&U 50 FLY"
        assert heatlist[0].heat == 1
        lane4 = heatlist[0].lane(4)
        assert lane4.name == "PERSON, JUST A"
        assert lane4.team == "TEAM"
        assert lane4.seed_time is None
        assert lane4.age is None
        assert lane4.is_empty is None
        assert lane4.is_dq is None
        lane6 = heatlist[0].lane(6)
        assert lane6.name == "BIGBIGBIGLY, NAMENAM"
        assert lane6.team == "LONGLONGLONGLONG"
        lane2 = heatlist[0].lane(2)
        assert lane2.is_empty is None

    def test_can_read_zero_heats(self, scb_zero_heats: io.StringIO):
        """Make sure we can read a file with no heats."""
        heatlist = _parse(scb_zero_heats)
        assert len(heatlist) == 0
