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
import logging
import os
import random
import shutil
import signal
import string
import threading
import time
import tkinter
from tkinter import DoubleVar, IntVar, StringVar
from typing import Callable, List

from model import Model

TESTING = False

logger = logging.getLogger(__name__)


def set_test_mode() -> None:
    """Set the application to test mode"""
    global TESTING  # pylint: disable=global-statement
    TESTING = True


class Scenario(abc.ABC):  # pylint: disable=too-few-public-methods
    """Base class for test actions"""

    @abc.abstractmethod
    def run(self) -> None:
        """Run the action"""


def run_scenario(scenario: Scenario) -> None:
    """Run a test scenario"""
    # Cause the application to exit if an exception occurs in the test thread
    old_hook = threading.excepthook

    def new_hook(*args, **kwargs):
        old_hook(*args, **kwargs)
        os.kill(os.getpid(), signal.SIGABRT)

    threading.excepthook = new_hook
    test_thread = threading.Thread(
        target=scenario.run, name="Test scenario", daemon=True
    )
    test_thread.start()


def build_random_scenario(
    model: Model, delay: float, seconds: float = 0, operations: int = 0
) -> Scenario:
    """Builds a test scenario that executes actions randomly"""

    # Prepare test data directories & result scenarios
    startlist_scenarios: List[Scenario] = []
    result_scenarios: List[Scenario] = []
    testdatadir = os.path.join(os.curdir, "testdata")
    testdata_exists = os.path.exists(testdatadir)
    tmp_startlist = os.path.join(testdatadir, "tmp_startlists")
    tmp_result = os.path.join(testdatadir, "tmp_result")

    latest_result_counter = Counter(model.latest_result)
    scoreboard_counter = Counter(model.scoreboard)

    if testdata_exists:
        os.makedirs(tmp_startlist, exist_ok=True)
        os.makedirs(tmp_result, exist_ok=True)
        model.enqueue(lambda: model.dir_startlist.set(tmp_startlist))
        model.enqueue(lambda: model.dir_results.set(tmp_result))
        startlist_scenarios = [
            AddStartlist(testdatadir, tmp_startlist),
            RemoveStartlist(tmp_startlist),
            GenDolphinCSV(model, tmp_startlist),
        ]
        result_scenarios = [
            AddDO4(
                testdatadir, tmp_result, [latest_result_counter, scoreboard_counter]
            ),
            RemoveDO4(tmp_result),
        ]

    appearance_scenarios: List[Scenario] = [
        SetInt(model, model.num_lanes, 6, 10),
        SetDouble(model, model.text_spacing, 0.8, 2.0),
        SetString(model, model.title, 0, 20),
    ]

    calculation_scenarios: List[Scenario] = [
        SetInt(model, model.min_times, 1, 3),
        SetDouble(model, model.time_threshold, 0.01, 3.0),
    ]

    return Sequentially(
        [
            Repeatedly(
                OneOf(
                    appearance_scenarios * 1
                    + calculation_scenarios * 2
                    + startlist_scenarios * 2
                    + result_scenarios * 20
                ),
                delay,
                seconds,
                operations,
            ),
            SimpleOp(model, model.menu_exit.run),
        ]
    )


def eventually(bool_fn: Callable[[], bool], interval_secs: float, tries: int) -> bool:
    """Check a boolean function until it returns true or we run out of tries"""
    for _ in range(tries):
        if bool_fn():
            return True
        time.sleep(interval_secs)
    return False


class Counter:  # pylint: disable=too-few-public-methods
    """A counter that tracks how often a Tk.Variable has been updated"""

    def __init__(self, var: tkinter.Variable) -> None:
        self._value = 0

        def update() -> None:
            self._value += 1

        var.trace_add("write", lambda *_: update())

    def get(self) -> int:
        """Get the counter's value"""
        return self._value


class Fail(Scenario):  # pylint: disable=too-few-public-methods
    """A scenario that always fails"""

    def run(self) -> None:
        assert False, "This scenario always fails"


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
            time.sleep(1 + random.expovariate(1.0 / self._delay))
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
        logger.info("Setting %s to %d", self._var, newvalue)
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
        logger.info("Setting %s to %f", self._var, newvalue)
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
        logger.info("Setting %s to %s", self._var, newvalue)
        self._model.enqueue(lambda: self._var.set(newvalue))


class AddStartlist(Scenario):  # pylint: disable=too-few-public-methods
    """Copy a startlist file into the startlists directory"""

    def __init__(self, testdatadir: str, startlistdir: str) -> None:
        """
        Copy a startlist file into the startlists directory

        :param testdatadir: the directory containing the main test data
        :param startlistdir: the directory for the startlists
        """
        super().__init__()
        self._testdatadir = testdatadir
        self._startlistdir = startlistdir

        # Ensure the directories exist
        assert os.path.isdir(self._testdatadir)
        assert os.path.isdir(self._startlistdir)

    def run(self) -> None:
        startlists_all = filter(
            lambda f: f.endswith(".scb"), os.listdir(self._testdatadir)
        )
        startlists_existing = filter(
            lambda f: f.endswith(".scb"), os.listdir(self._startlistdir)
        )
        startlists_new = set(startlists_all) - set(startlists_existing)
        if len(startlists_new) > 0:
            startlist = random.choice(list(startlists_new))
            logger.info("Adding startlist %s", startlist)
            shutil.copy(os.path.join(self._testdatadir, startlist), self._startlistdir)


class RemoveStartlist(Scenario):  # pylint: disable=too-few-public-methods
    """Remove a startlist file from the startlists directory"""

    def __init__(self, startlistdir: str) -> None:
        """
        Remove a startlist file from the startlists directory

        :param startlistdir: the directory for the startlists
        """
        super().__init__()
        self._startlistdir = startlistdir

        # Ensure the directory exists
        assert os.path.isdir(self._startlistdir)

    def run(self) -> None:
        startlists = list(
            filter(lambda f: f.endswith(".scb"), os.listdir(self._startlistdir))
        )
        if len(startlists) > 0:
            startlist = random.choice(startlists)
            logger.info("Removing startlist %s", startlist)
            os.remove(os.path.join(self._startlistdir, startlist))


class AddDO4(Scenario):  # pylint: disable=too-few-public-methods
    """Copy a do4 file into the do4 directory"""

    def __init__(self, testdatadir: str, do4dir: str, counters: List[Counter]) -> None:
        """
        Copy a do4 file into the do4 directory

        :param testdatadir: the directory containing the main test data
        :param do4dir: the directory for the do4 files
        :param update_counter: the counter for the number of updates to the results
        """
        super().__init__()
        self._testdatadir = testdatadir
        self._do4dir = do4dir
        self._counters = counters

        # Ensure the directories exist
        assert os.path.isdir(self._testdatadir)
        assert os.path.isdir(self._do4dir)

    def run(self) -> None:
        do4_all = filter(lambda f: f.endswith(".do4"), os.listdir(self._testdatadir))
        do4_existing = filter(lambda f: f.endswith(".do4"), os.listdir(self._do4dir))
        do4_new = set(do4_all) - set(do4_existing)
        if len(do4_new) > 0:
            do4 = random.choice(list(do4_new))
            logger.info("Adding do4 %s", do4)
            prev_count = []
            for counter in self._counters:
                prev_count.append(counter.get())
            shutil.copy(os.path.join(self._testdatadir, do4), self._do4dir)
            for i in range(len(self._counters)):
                assert eventually(
                    # i=i is a hack to capture the current value of i
                    lambda i=i: self._counters[i].get() > prev_count[i],  # type: ignore
                    0.1,
                    50,
                )


class RemoveDO4(Scenario):  # pylint: disable=too-few-public-methods
    """Remove a do4 file from the do4 directory"""

    def __init__(self, do4dir: str) -> None:
        """
        Remove a do4 file from the do4 directory

        :param do4dir: the directory for the do4 files
        """
        super().__init__()
        self._do4dir = do4dir

        # Ensure the directory exists
        assert os.path.isdir(self._do4dir)

    def run(self) -> None:
        do4list = list(filter(lambda f: f.endswith(".do4"), os.listdir(self._do4dir)))
        if len(do4list) > 0:
            do4 = random.choice(do4list)
            logger.info("Removing do4 %s", do4)
            os.remove(os.path.join(self._do4dir, do4))


class GenDolphinCSV(Scenario):  # pylint: disable=too-few-public-methods
    """Generate the dolphin event CSV file and verify its contents"""

    def __init__(self, model: Model, startlistdir: str) -> None:
        """
        Generate the dolphin event CSV file and verify its contents

        :param model: the application model
        :param startlistdir: the directory for the startlists
        """
        super().__init__()
        self._model = model
        self._startlistdir = startlistdir

        # Ensure the directory exists
        assert os.path.isdir(self._startlistdir)

    def run(self) -> None:
        logger.info("Checking CSV")
        # Trigger event CSV export
        self._model.enqueue(self._model.dolphin_export.run)
        num_startlists = len(
            list(filter(lambda f: f.endswith(".scb"), os.listdir(self._startlistdir)))
        )
        # Ensure the CSV has on entry for each event
        assert eventually(lambda: num_startlists == len(self._read_csv()), 0.1, 50)

    def _read_csv(self) -> List[str]:
        filename = os.path.join(self._startlistdir, "dolphin_events.csv")
        try:
            with open(filename, "r", encoding="cp1252") as file:
                lines = file.readlines()
                return lines
        except FileNotFoundError:
            return []
