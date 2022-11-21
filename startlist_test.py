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

'''Tests for StartList class'''

import io
import textwrap
import pytest

from startlist import StartList

def test_two_heats():
    '''General test on 2 heats worth of data'''
    slist = StartList(io.StringIO(textwrap.dedent("""\
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
                            --                """)))
    assert slist.event_name == "BOYS 10&U 50 FLY"

    assert not slist.is_empty_lane(1, 4)
    assert slist.entry(1, 4).name == "PERSON, JUST A"
    assert slist.entry(1, 4).team == "TEAM"

    assert slist.is_empty_lane(1, 5)

    assert slist.entry(1, 6).name == "BIGBIGBIGLY, NAMENAM"
    assert slist.entry(1, 6).team == "LONGLONGLONGLONG"

    assert slist.entry(2, 4).name == "XXXXXXX, YYYYYY Z"
    assert slist.entry(2, 4).team == ""

    assert slist.entry(2, 6).name == "AAAAA, B"
    assert slist.entry(2, 6).team == "X"

def test_six_heats():
    '''General test on 6 heats worth of data'''
    slist = StartList(io.StringIO(textwrap.dedent("""\
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
                            --                """)))
    assert slist.event_num == 34
    assert slist.event_name == "GIRLS 15&O 50 BACK"
    assert slist.heats == 6
    assert slist.is_empty_lane(1, 1)
    assert not slist.is_empty_lane(6, 8)
    assert slist.is_empty_lane(6, 10)

def test_invalid_header():
    '''Exception should be thrown when header can't be parsed'''
    with pytest.raises(ValueError) as verr:
        StartList(io.StringIO(textwrap.dedent("""\
            #AA BOYS 10&U 50 FLY
                                --                
                                --                
                                --                
            PERSON, JUST A      --TEAM            
                                --                
            BIGBIGBIGLY, NAMENAM--LONGLONGLONGLONG
                                --                
                                --                
                                --                
                                --                """)))
    assert verr.match(r'Unable to parse header')

def test_invalid_num_lanes():
    '''Exception should be thrown when there are not 10 lanes per heat'''
    with pytest.raises(ValueError) as verr:
        StartList(io.StringIO(textwrap.dedent("""\
            #1 BOYS 10&U 50 FLY
                                --                
                                --                
                                --                
            PERSON, JUST A      --TEAM            
                                --                
            BIGBIGBIGLY, NAMENAM--LONGLONGLONGLONG
                                --                
                                --                
                                --                """)))
    assert verr.match(r'Length is not a multiple of 10')

def test_invalid_line():
    '''Exception should be thrown when a line can't be parsed as an entry'''
    with pytest.raises(ValueError) as verr:
        StartList(io.StringIO(textwrap.dedent("""\
            #1 BOYS 10&U 50 FLY
                                --                
            INVALID LINE
                                --                
            PERSON, JUST A      --TEAM            
                                --                
            BIGBIGBIGLY, NAMENAM--LONGLONGLONGLONG
                                --                
                                --                
                                --                
                                --                """)))
    assert verr.match(r'Unable to parse line')
