#! /usr/bin/env python
# Wahoo! Results - https://github.com/JohnStrunk/wahoo-results
# Copyright (C) 2023 - John D. Strunk
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

"""Test harness for Wahoo Results"""

import abc
import random
import threading
import time
from tkinter import IntVar
from typing import Callable, List

from model import Model

# How long to pause beween test actions
MEAN_ARRIVAL_SECONDS = 1.0


class Tester(threading.Thread):
    """Test harness for Wahoo Results"""

    def __init__(self, model: Model, duration: float = 0) -> None:
        super().__init__(name="Tester", daemon=True)
        self._model = model
        self._duration = duration

    def enqueue(self, func: Callable[[], None]) -> None:
        """Enqueue a function to be run on the main thread"""
        self._model.enqueue(func)

    def run(self) -> None:
        # The list of potential test actions to run
        actions: List[Action] = [
            # SimpleOp(self, self._model.menu_exit.run),
            SetInt(self, self._model.num_lanes, 6, 10),
        ]
        stop_time = time.time() + self._duration
        while time.time() < stop_time or self._duration == 0:
            random.choice(actions).run()
            time.sleep(random.expovariate(1.0 / MEAN_ARRIVAL_SECONDS))
        # Exit the application
        self.enqueue(self._model.menu_exit.run)


class Action(abc.ABC):  # pylint: disable=too-few-public-methods
    """Base class for test actions"""

    def __init__(self, tester: Tester) -> None:
        self._tester = tester

    @abc.abstractmethod
    def run(self) -> None:
        """Run the action"""


class SimpleOp(Action):  # pylint: disable=too-few-public-methods
    """A test operation that runs a function"""

    def __init__(self, tester: Tester, func: Callable[[], None]) -> None:
        """A simple operation that just runs a function"""
        super().__init__(tester)
        self._fn = func

    def run(self) -> None:
        self._tester.enqueue(self._fn)


class SetInt(Action):  # pylint: disable=too-few-public-methods
    """Set an integer variable to a random value"""

    def __init__(self, tester: Tester, var: IntVar, minimum: int, maximum: int) -> None:
        """
        Set an integer variable to a random value

        :param tester: the test runner
        :param var: the integer variable to set
        :param minimum: the minimum value to choose
        :param maximum: the maximum value to choose
        """
        super().__init__(tester)
        self._var = var
        self._min = minimum
        self._max = maximum

    def run(self) -> None:
        newvalue = random.randint(self._min, self._max)
        print(f"Setting {self._var} to {newvalue}")
        self._tester.enqueue(lambda: self._var.set(newvalue))
