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
import string
import threading
import time
from tkinter import DoubleVar, IntVar, StringVar
from typing import Callable, List, Optional

from model import Model

TESTING = False


def set_test_mode() -> None:
    """Set the application to test mode"""
    global TESTING  # pylint: disable=global-statement
    TESTING = True


class Scenario(abc.ABC):  # pylint: disable=too-few-public-methods
    """Base class for test actions"""

    def __init__(self) -> None:
        pass

    @abc.abstractmethod
    def run(self) -> None:
        """Run the action"""


def run_scenario(scenario: Scenario) -> None:
    """Run a test scenario"""
    test_thread = threading.Thread(
        target=scenario.run, name="Test scenario", daemon=True
    )
    test_thread.start()


def build_random_scenario(
    model: Model, delay: float, seconds: float = 0, operations: int = 0
) -> Scenario:
    """Builds a test scenario that executes actions randomly"""
    return Sequentially(
        [
            Repeatedly(
                OneOf(
                    [
                        SetInt(model, model.num_lanes, 6, 10),
                        SetInt(model, model.min_times, 1, 3),
                        SetDouble(model, model.time_threshold, 0.01, 3.0),
                        SetDouble(model, model.text_spacing, 0.8, 2.0),
                        SetString(model, model.title, 0, 20),
                    ]
                ),
                delay,
                seconds,
                operations,
            ),
            SimpleOp(model, model.menu_exit.run),
        ]
    )


class Repeatedly(Scenario):  # pylint: disable=too-few-public-methods
    """Run an action repeatedly"""

    def __init__(
        self, action: Scenario, delay: float, seconds: float, operations: int
    ) -> None:
        """
        Run an action repeatedly

        :param action: The scenario to run
        :param delay: The mean delay between actions
        :param seconds: The maximum number of seconds to run (0: run forever)
        :param operations: The maximum number of operations to run (0: run forever)
        """
        super().__init__()
        self._delay = delay
        self._seconds = seconds
        self._operations = operations
        self._action = action

    def run(self) -> None:
        start = time.time()
        total_ops = 0
        while (self._seconds == 0 or time.time() - start < self._seconds) and (
            self._operations == 0 or self._operations > total_ops
        ):
            self._action.run()
            time.sleep(random.expovariate(1.0 / self._delay))
            total_ops += 1


class Sequentially(Scenario):  # pylint: disable=too-few-public-methods
    """Run each item in a list of actions"""

    def __init__(self, actions: List[Scenario]) -> None:
        super().__init__()
        self._actions = actions

    def run(self) -> None:
        for action in self._actions:
            action.run()


class OneOf(Scenario):  # pylint: disable=too-few-public-methods
    """Randomly choose one of a list of actions to run"""

    def __init__(self, actions: List[Scenario]) -> None:
        super().__init__()
        self._actions = actions

    def run(self) -> None:
        random.choice(self._actions).run()


class SimpleOp(Scenario):  # pylint: disable=too-few-public-methods
    """A test operation that runs a function"""

    def __init__(self, model: Model, func: Callable[[], None]) -> None:
        """A simple operation that just runs a function"""
        super().__init__()
        self._model = model
        self._fn = func

    def run(self) -> None:
        self._model.enqueue(self._fn)


class SetInt(Scenario):  # pylint: disable=too-few-public-methods
    """Set an integer variable to a random value"""

    def __init__(self, model: Model, var: IntVar, minimum: int, maximum: int) -> None:
        """
        Set an integer variable to a random value

        :param model: the application model
        :param var: the integer variable to set
        :param minimum: the minimum value to choose
        :param maximum: the maximum value to choose
        """
        super().__init__()
        self._model = model
        self._var = var
        self._min = minimum
        self._max = maximum

    def run(self) -> None:
        newvalue = random.randint(self._min, self._max)
        print(f"Setting {self._var} to {newvalue}")
        self._model.enqueue(lambda: self._var.set(newvalue))


class SetDouble(Scenario):  # pylint: disable=too-few-public-methods
    """Set a double variable to a random value"""

    def __init__(
        self, model: Model, var: DoubleVar, minimum: float, maximum: float
    ) -> None:
        """
        Set a double variable to a random value

        :param model: the application model
        :param var: the variable to set
        :param minimum: the minimum value to choose
        :param maximum: the maximum value to choose
        """
        super().__init__()
        self._model = model
        self._var = var
        self._min = minimum
        self._max = maximum

    def run(self) -> None:
        newvalue = random.random() * (self._max - self._min) + self._min
        print(f"Setting {self._var} to {newvalue}")
        self._model.enqueue(lambda: self._var.set(newvalue))


class SetString(Scenario):  # pylint: disable=too-few-public-methods
    """Set a string variable to a random value"""

    def __init__(
        self, model: Model, var: StringVar, length_min: int, length_max: int
    ) -> None:
        """
        Set a string variable to a random value

        :param model: the application model
        :param var: the variable to set
        :param values: the list of values to choose from
        """
        super().__init__()
        self._model = model
        self._var = var
        self._min = length_min
        self._max = length_max

    def run(self) -> None:
        newvalue = "".join(
            random.choice(
                string.ascii_letters + string.digits + string.punctuation + " "
            )
            for _ in range(random.randint(self._min, self._max))
        )
        print(f"Setting {self._var} to {newvalue}")
        self._model.enqueue(lambda: self._var.set(newvalue))
