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

"""Test harness for Wahoo Results."""

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
from functools import reduce
from tkinter import DoubleVar, IntVar, StringVar
from typing import Callable, List

from model import Model

TESTING = False

logger = logging.getLogger(__name__)


def set_test_mode() -> None:
    """Set the application to test mode."""
    global TESTING  # noqa: PLW0603
    TESTING = True


class Scenario(abc.ABC):
    """Base class for test actions."""

    @abc.abstractmethod
    def run(self) -> None:
        """Run the action."""


def run_scenario(scenario: Scenario) -> None:
    """Run a test scenario."""
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


def build_scenario(model: Model, test: str) -> Scenario:
    """Build a test scenario from a description.

    :param model: The application model
    :param test: The test description
    """
    test_name = test.split(":")[0]
    if test_name == "chromecast":
        [delay, seconds, operations] = test.split(":")[1:]
        return _build_cc_scenario(model, float(delay), float(seconds), int(operations))
    if test_name == "scripted":
        [seconds] = test.split(":")[1:]
        return _build_scripted_scenario(model, float(seconds))
    if test_name == "random":
        [delay, seconds, operations] = test.split(":")[1:]
        return _build_random_scenario(
            model, float(delay), float(seconds), int(operations)
        )
    raise ValueError(f"Unknown test: {test}")


def _build_cc_scenario(
    model: Model, delay: float, seconds: float, operations: int
) -> Scenario:
    """Build a test scenario that manipulates the Chromecast connections.

    :param model: The model
    :param delay: The mean delay between actions
    :param seconds: The amount of time to perform testing (0: run forever)
    :param operations: The maximum number of operations to perform (0: run forever)
    :returns: The test scenario
    """
    return Sequentially(
        [
            Delay(2),  # Wait for the application to start
            ############################################################
            Repeatedly(
                ToggleChromecast(model),
                delay,
                seconds,
                operations,
            ),
            Enqueue(model, model.menu_exit.run),
        ]
    )


def _build_scripted_scenario(model: Model, seconds: float) -> Scenario:
    """Build a test scenario that executes a pre-defined sequence of actions.

    :param model: The model
    :param seconds: The amount of time to perform randomized testing
    :returns: The test scenario
    """
    testdatadir = os.path.join(os.curdir, "testdata")
    testdata_exists = os.path.exists(testdatadir)
    tmp_startlist = os.path.join(testdatadir, "tmp_startlists")
    tmp_result = os.path.join(testdatadir, "tmp_result")

    latest_result_counter = Counter(model.latest_result)
    scoreboard_counter = Counter(model.scoreboard)

    # Ensure the test data is present, and clean out the temporary directories
    assert testdata_exists, "Test data directory does not exist"
    time.sleep(2)
    for dirname in [tmp_startlist, tmp_result]:
        try:
            shutil.rmtree(dirname)
            logger.debug("Removed directory: %s", dirname)
        except FileNotFoundError:
            pass
        os.makedirs(dirname)
        logger.debug("Created directory: %s", dirname)
    time.sleep(2)
    model.enqueue(lambda: model.dir_startlist.set(tmp_startlist))
    model.enqueue(lambda: model.dir_results.set(tmp_result))

    return Sequentially(
        [
            Delay(2),  # Wait for the application to start
            ############################################################
            ## Set configuration for the tests
            Enqueue(model, lambda: model.title.set("Test Title")),  # Set the title
            Enqueue(model, lambda: model.text_spacing.set(1.1)),  # Set the text spacing
            Enqueue(model, lambda: model.num_lanes.set(6)),  # Set the number of lanes
            Enqueue(model, lambda: model.min_times.set(2)),  # Set the minimum times
            Enqueue(
                model,
                lambda: model.time_threshold.set(0.30),  # Set the time threshold
            ),
            ############################################################
            ## Validate creation of event CSV file
            LoadAllSCB(testdatadir, tmp_startlist),  # Make all startlists available
            GenDolphinCSV(model, tmp_startlist),  # Generate the Dolphin CSV file
            ############################################################
            ## Test specific scenarios
            # Race w/ 6 lanes, names, all valid times
            AddDO4(
                testdatadir,
                tmp_result,
                "010-223-003A-0020.do4",
                [latest_result_counter, scoreboard_counter],
            ),
            Validate(
                lambda: model.latest_result.get().has_names(),  # type: ignore
                "SCB should have an entry for the heat/event",
            ),
            Validate(
                # list comp creates a list of booleans, one for each lane (do
                # they have a name?), reduce ands them together, ensuring that
                # if any don't have a name, the result is false
                lambda: reduce(
                    lambda a, b: a and b,
                    [
                        len(model.latest_result.get().lane(i).name) > 0  # type: ignore
                        for i in range(1, 6)
                    ],
                ),
                "All lanes should have a name",
            ),
            Validate(
                lambda: reduce(
                    lambda a, b: a and b,
                    [
                        model.latest_result.get().lane(i).final_time is not None  # type: ignore
                        for i in range(1, 6)
                    ],
                ),
                "All lanes should have valid final times",
            ),
            # Race w/ a no-show
            AddDO4(
                testdatadir,
                tmp_result,
                "010-214-001A-0068.do4",
                [latest_result_counter, scoreboard_counter],
            ),
            Validate(
                lambda: model.latest_result.get().has_names(),  # type: ignore
                "SCB should have an entry for the heat/event",
            ),
            Validate(
                lambda: not model.latest_result.get().lane(2).is_noshow,  # type: ignore
                "Lane 2 IS NOT a no-show",
            ),
            Validate(
                lambda: model.latest_result.get().lane(5).is_noshow,  # type: ignore
                "Lane 5 IS a no-show",
            ),
            # Race w/ an unexpected swimmer (no name)
            AddDO4(
                testdatadir,
                tmp_result,
                "001-011-001A-0015.do4",
                [latest_result_counter, scoreboard_counter],
            ),
            Validate(
                lambda: model.latest_result.get().has_names(),  # type: ignore
                "SCB should have an entry for the heat/event",
            ),
            Validate(
                lambda: len(model.latest_result.get().lane(1).name) == 0,  # type: ignore
                "Lane 1 should not have a name",
            ),
            Validate(
                lambda: model.latest_result.get().lane(1).final_time is not None,  # type: ignore
                "Lane 1 should have a valid time",
            ),
            # Race w/ an extra heat (no names)
            AddDO4(
                testdatadir,
                tmp_result,
                "001-011-002A-0016.do4",
                [latest_result_counter, scoreboard_counter],
            ),
            Validate(
                lambda: model.latest_result.get().lane(3).name is None,  # type: ignore
                "SCB should NOT have names for the heat",
            ),
            Validate(
                lambda: model.latest_result.get().lane(3).final_time is not None,  # type: ignore
                "Lane 3 should have a valid time",
            ),
            # Race w/o a corresponding scb file
            AddDO4(
                testdatadir,
                tmp_result,
                "001-042-001A-0077.do4",
                [latest_result_counter, scoreboard_counter],
            ),
            Validate(
                lambda: not model.latest_result.get().has_names(),  # type: ignore
                "There should not be an SCB for the event",
            ),
            Validate(
                lambda: model.latest_result.get().lane(3).final_time is not None,  # type: ignore
                "Lane 3 should have a valid time",
            ),
            # Race w/ too much time delta
            AddDO4(
                testdatadir,
                tmp_result,
                "046-111-004A-0049.do4",
                [latest_result_counter, scoreboard_counter],
            ),
            Validate(
                lambda: model.latest_result.get().has_names(),  # type: ignore
                "SCB should have an entry for the heat/event",
            ),
            Validate(
                lambda: model.latest_result.get().lane(3).final_time is None,  # type: ignore
                "Lane 3 should not have a valid time (2 times differ by greater than threshold)",
            ),
            Validate(
                lambda: not model.latest_result.get().lane(3).is_noshow,  # type: ignore
                "Lane 3 IS NOT a no-show",
            ),
            # Race w/ too few watch times
            AddDO4(
                testdatadir,
                tmp_result,
                "046-111-003A-0048.do4",
                [latest_result_counter, scoreboard_counter],
            ),
            Validate(
                lambda: model.latest_result.get().has_names(),  # type: ignore
                "SCB should have an entry for the heat/event",
            ),
            Validate(
                lambda: model.latest_result.get().lane(1).final_time is None,  # type: ignore
                "Lane 1 should not have a valid time (only 1 watch time, threshold is 2)",
            ),
            Validate(
                lambda: not model.latest_result.get().lane(1).is_noshow,  # type: ignore
                "Lane 1 IS NOT a no-show",
            ),
            Validate(
                lambda: model.latest_result.get().lane(2).final_time is not None,  # type: ignore
                "Lane 2 should have a valid time",
            ),
            ############################################################
            ## Perform some random actions
            Repeatedly(  # Add a bunch of results
                OneOf(
                    [
                        AddRandomDO4(
                            testdatadir,
                            tmp_result,
                            [latest_result_counter, scoreboard_counter],
                        ),
                        RemoveRandomDO4(tmp_result),
                        AddStartlist(testdatadir, tmp_startlist),
                        RemoveStartlist(tmp_startlist),
                        GenDolphinCSV(model, tmp_startlist),
                    ],
                ),
                0.5,
                seconds,
                0,
            ),
            Enqueue(model, model.menu_exit.run),  # Exit the application
        ]
    )


def _build_random_scenario(
    model: Model, delay: float, seconds: float = 0, operations: int = 0
) -> Scenario:
    """Build a test scenario that executes actions randomly.

    :param model: The application model
    :param delay: The mean delay between actions
    :param seconds: The amount of time to perform randomized testing (0: run forever)
    :param operations: The maximum number of operations to perform (0: run forever)
    :returns: The test scenario
    """
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
            AddRandomDO4(
                testdatadir, tmp_result, [latest_result_counter, scoreboard_counter]
            ),
            RemoveRandomDO4(tmp_result),
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
                    + [ToggleChromecast(model)] * 1
                    + calculation_scenarios * 2
                    + startlist_scenarios * 2
                    + result_scenarios * 20
                ),
                delay,
                seconds,
                operations,
            ),
            Enqueue(model, model.menu_exit.run),
        ]
    )


def eventually(bool_fn: Callable[[], bool], interval_secs: float, tries: int) -> bool:
    """Check a boolean function until it returns true or we run out of tries.

    :param bool_fn: The function to check
    :param interval_secs: The time between checks
    :param tries: The number of tries before giving up
    :returns: True if the function returned true, False otherwise
    """
    for i in range(tries):
        if bool_fn():
            logger.debug("Eventually() passed in %0.1f seconds", interval_secs * i)
            return True
        time.sleep(interval_secs)
    logger.debug("Eventually() failed in %0.1f seconds", interval_secs * tries)
    return False


class Counter:
    """A counter that tracks how often a Tk.Variable has been updated."""

    def __init__(self, var: tkinter.Variable) -> None:
        """Create a counter that tracks the number of times a Tk.Variable is updated.

        :param var: The Tk.Variable to track
        """
        self._value = 0
        self._var = var

        def update() -> None:
            self._value += 1

        self._cbname = var.trace_add("write", lambda *_: update())

    def __del__(self) -> None:
        """Remove the trace callback."""
        if self._cbname:
            self._var.trace_remove("write", self._cbname)

    def get(self) -> int:
        """Get the counter's value."""
        return self._value


class Delay(Scenario):
    """A scenario that does nothing for a specified amount of time."""

    def __init__(self, seconds: float) -> None:
        """Create a scenario that pauses for a specified amount of time.

        :param seconds: The number of seconds to pause
        """
        super().__init__()
        self._seconds = seconds

    def run(self) -> None:
        """Pause for the specified amount of time."""
        logger.info("Delaying for %f seconds", self._seconds)
        time.sleep(self._seconds)


class Fail(Scenario):
    """A scenario that always fails."""

    def run(self) -> None:
        """Run the scenario."""
        assert False, "This scenario always fails"


class Repeatedly(Scenario):
    """Run an action repeatedly."""

    def __init__(
        self, action: Scenario, delay: float, seconds: float, operations: int
    ) -> None:
        """Run an action repeatedly.

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
        """Run the scenario."""
        start = time.time()
        total_ops = 0
        while (self._seconds == 0 or time.time() - start < self._seconds) and (
            self._operations == 0 or self._operations > total_ops
        ):
            self._action.run()
            time.sleep(random.expovariate(1.0 / self._delay))
            total_ops += 1


class Sequentially(Scenario):
    """Run each item in a list of actions."""

    def __init__(self, actions: List[Scenario]) -> None:
        """Create a scenario that runs each action in a list.

        :param actions: The list of actions to run
        """
        super().__init__()
        self._actions = actions

    def run(self) -> None:
        """Run the scenario."""
        for action in self._actions:
            action.run()


class OneOf(Scenario):
    """Randomly choose one of a list of actions to run."""

    def __init__(self, actions: List[Scenario]) -> None:
        """Create a scenario that randomly chooses one of the actions to run.

        :param actions: The list of actions to choose from
        """
        super().__init__()
        self._actions = actions

    def run(self) -> None:
        """Run the scenario."""
        random.choice(self._actions).run()


class Enqueue(Scenario):
    """A test operation that runs a function in the main thread."""

    def __init__(self, model: Model, func: Callable[[], None]) -> None:
        """Enqueue an operation that runs a function in the main thread.

        Note: The function is run asynchronously in the main thread, so it must
        not block, and it will not block the test thread.

        :param model: the application model
        :param func: the function to run
        """
        super().__init__()
        self._model = model
        self._fn = func

    def run(self) -> None:
        """Run the operation."""
        logger.info("Enqueuing function to run in main thread")
        self._model.enqueue(self._fn)


class Validate(Scenario):
    """A test operation that runs a function."""

    def __init__(self, func: Callable[[], bool], message: str = "") -> None:
        """Run a function inline.

        :param func: the function to run
        :param message: the message to log when the function fails
        """
        super().__init__()
        self._fn = func
        self._message = message

    def run(self) -> None:
        """Run the operation."""
        logger.info("Validating: %s", self._message)
        assert self._fn(), self._message


class SetInt(Scenario):
    """Set an integer variable to a random value."""

    def __init__(self, model: Model, var: IntVar, minimum: int, maximum: int) -> None:
        """Set an integer variable to a random value.

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
        """Set the variable."""
        newvalue = random.randint(self._min, self._max)
        logger.info("Setting %s to %d", self._var, newvalue)
        self._model.enqueue(lambda: self._var.set(newvalue))


class SetDouble(Scenario):
    """Set a double variable to a random value."""

    def __init__(
        self, model: Model, var: DoubleVar, minimum: float, maximum: float
    ) -> None:
        """Set a double variable to a random value.

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
        """Set the variable."""
        newvalue = random.random() * (self._max - self._min) + self._min
        logger.info("Setting %s to %f", self._var, newvalue)
        self._model.enqueue(lambda: self._var.set(newvalue))


class SetString(Scenario):
    """Set a string variable to a random value."""

    def __init__(
        self, model: Model, var: StringVar, length_min: int, length_max: int
    ) -> None:
        """Set a string variable to a random value.

        :param model: the application model
        :param var: the variable to set
        :param length_min: the minimum length of the string
        :param length_max: the maximum length of the string
        """
        super().__init__()
        self._model = model
        self._var = var
        self._min = length_min
        self._max = length_max

    def run(self) -> None:
        """Set the variable."""
        newvalue = "".join(
            random.choice(
                string.ascii_letters + string.digits + string.punctuation + " "
            )
            for _ in range(random.randint(self._min, self._max))
        )
        logger.info("Setting %s to %s", self._var, newvalue)
        self._model.enqueue(lambda: self._var.set(newvalue))


class AddStartlist(Scenario):
    """Copy a startlist file into the startlists directory."""

    def __init__(self, testdatadir: str, startlistdir: str) -> None:
        """Copy a startlist file into the startlists directory.

        :param testdatadir: the directory containing the main test data
        :param startlistdir: the destination directory for the startlists
        """
        super().__init__()
        self._testdatadir = testdatadir
        self._startlistdir = startlistdir

        # Ensure the directories exist
        assert os.path.isdir(self._testdatadir), (
            "Test data directory does not exist or is not a directory"
        )
        assert os.path.isdir(self._startlistdir), (
            "Startlist directory does not exist or is not a directory"
        )

    def run(self) -> None:
        """Copy a random startlist file."""
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


class RemoveStartlist(Scenario):
    """Remove a startlist file from the startlists directory."""

    def __init__(self, startlistdir: str) -> None:
        """Remove a startlist file from the startlists directory.

        :param startlistdir: the directory for the startlists
        """
        super().__init__()
        self._startlistdir = startlistdir

        # Ensure the directory exists
        assert os.path.isdir(self._startlistdir), "Startlist directory does not exist"

    def run(self) -> None:
        """Remove a random startlist file."""
        startlists = list(
            filter(lambda f: f.endswith(".scb"), os.listdir(self._startlistdir))
        )
        if len(startlists) > 0:
            startlist = random.choice(startlists)
            logger.info("Removing startlist %s", startlist)
            os.remove(os.path.join(self._startlistdir, startlist))


class AddDO4(Scenario):
    """Copy a specific do4 file into the do4 directory."""

    def __init__(
        self, testdatadir: str, do4dir: str, do4: str, counters: List[Counter]
    ) -> None:
        """Copy a do4 file into the do4 directory.

        :param testdatadir: the directory containing the main test data
        :param do4dir: the directory for the do4 files
        :param do4: the do4 file to copy
        :param counters: the counters used to verify the do4 file was processed
        """
        super().__init__()
        self._testdatadir = testdatadir
        self._do4dir = do4dir
        self._do4 = do4
        self._counters = counters

        # Ensure the directories exist
        assert os.path.isdir(self._testdatadir), "Test data directory does not exist"
        assert os.path.isdir(self._do4dir), "DO4 directory does not exist"
        assert os.path.isfile(os.path.join(self._testdatadir, self._do4)), (
            "DO4 file does not exist or is not a file"
        )

    def run(self) -> None:
        """Perform the copy."""
        logger.info("Adding do4 %s", self._do4)
        prev_count = []
        for counter in self._counters:
            prev_count.append(counter.get())
        shutil.copy(os.path.join(self._testdatadir, self._do4), self._do4dir)
        for i in range(len(self._counters)):
            assert eventually(
                # i=i is a hack to capture the current value of i
                lambda i=i: self._counters[i].get() > prev_count[i],
                0.1,
                100,
            ), "DO4 file was not processed"


class AddRandomDO4(Scenario):
    """Copy a random do4 file into the do4 directory."""

    def __init__(self, testdatadir: str, do4dir: str, counters: List[Counter]) -> None:
        """Copy a random do4 file into the do4 directory.

        :param testdatadir: the directory containing the main test data
        :param do4dir: the directory for the do4 files
        :param counters: the counters used to verify the do4 file was processed
        """
        super().__init__()
        self._testdatadir = testdatadir
        self._do4dir = do4dir
        self._counters = counters

        # Ensure the directories exist
        assert os.path.isdir(self._testdatadir), "Test data directory does not exist"
        assert os.path.isdir(self._do4dir), "DO4 directory does not exist"

    def run(self) -> None:
        """Copy a random do4 file."""
        do4_all = filter(lambda f: f.endswith(".do4"), os.listdir(self._testdatadir))
        do4_existing = filter(lambda f: f.endswith(".do4"), os.listdir(self._do4dir))
        do4_new = set(do4_all) - set(do4_existing)
        if len(do4_new) > 0:
            do4 = random.choice(list(do4_new))
            AddDO4(self._testdatadir, self._do4dir, do4, self._counters).run()


class RemoveRandomDO4(Scenario):
    """Remove a do4 file from the do4 directory."""

    def __init__(self, do4dir: str) -> None:
        """Remove a do4 file from the do4 directory.

        :param do4dir: the directory for the do4 files
        """
        super().__init__()
        self._do4dir = do4dir

        # Ensure the directory exists
        assert os.path.isdir(self._do4dir), "DO4 directory does not exist"

    def run(self) -> None:
        """Remove a random do4 file."""
        do4list = list(filter(lambda f: f.endswith(".do4"), os.listdir(self._do4dir)))
        if len(do4list) > 0:
            do4 = random.choice(do4list)
            logger.info("Removing do4 %s", do4)
            os.remove(os.path.join(self._do4dir, do4))


class GenDolphinCSV(Scenario):
    """Generate the dolphin event CSV file and verify its contents."""

    def __init__(self, model: Model, startlistdir: str) -> None:
        """Generate the dolphin event CSV file and verify its contents.

        :param model: the application model
        :param startlistdir: the directory for the startlists
        """
        super().__init__()
        self._model = model
        self._startlistdir = startlistdir

        # Ensure the directory exists
        assert os.path.isdir(self._startlistdir), "Startlist directory does not exist"

    def run(self) -> None:
        """Generate the CSV file and verify its contents."""
        logger.info("Checking CSV")
        # Trigger event CSV export
        self._model.enqueue(self._model.dolphin_export.run)
        _FlushQueue(self._model).run()  # Ensure the queue is serviced before checking
        # Only count SCB files that have at least 1 heat
        num_startlists = 0
        files = list(
            filter(lambda f: f.endswith(".scb"), os.listdir(self._startlistdir))
        )
        for file in files:
            file_path = os.path.join(self._startlistdir, file)
            with open(file_path, "r", encoding="cp1252") as scb_file:
                lines = scb_file.readlines()
                if len(lines) > 10:  # noqa: PLR2004
                    num_startlists += 1

        assert eventually(lambda: num_startlists == len(self._read_csv()), 0.1, 100), (
            "The CSV file does not contain the expected number of events"
        )

    def _read_csv(self) -> List[str]:
        filename = os.path.join(self._startlistdir, "dolphin_events.csv")
        try:
            with open(filename, "r", encoding="cp1252") as file:
                lines = file.readlines()
                return lines
        except FileNotFoundError:
            return []


class LoadAllSCB(Scenario):
    """Load all SCB files in the startlists directory."""

    def __init__(self, testdatadir: str, startlistdir: str) -> None:
        """Load all SCB files in the startlists directory.

        :param testdatadir: the directory containing the main test data
        :param startlistdir: the directory for the startlists
        """
        super().__init__()
        self._testdatadir = testdatadir
        self._startlistdir = startlistdir

        # Ensure the directories exist
        assert os.path.isdir(self._testdatadir), "Test data directory does not exist"
        assert os.path.isdir(self._startlistdir), (
            "The startlist directory does not exist"
        )

    def run(self) -> None:
        """Load the SCB files."""
        startlists = list(
            filter(lambda f: f.endswith(".scb"), os.listdir(self._testdatadir))
        )
        logger.info("Loading all %d SCB files", len(startlists))
        for startlist in startlists:
            logger.info("Loading SCB %s", startlist)
            shutil.copy(os.path.join(self._testdatadir, startlist), self._startlistdir)


class EnableChromecast(Scenario):
    """Enable a random Chromecast device."""

    def __init__(self, model: Model) -> None:
        """Enable a random Chromecast device.

        :param model: the application model
        """
        super().__init__()
        self._model = model

    def run(self) -> None:
        """Enable a random Chromecast device."""
        devices = self._model.cc_status.get()
        disabled_devices = list(filter(lambda d: not d.enabled, devices))
        if len(disabled_devices) > 0:
            device = random.choice(disabled_devices)
            logger.info("Enabling chromecast %s", device.name)
            for dev in devices:
                if dev.name == device.name:
                    dev.enabled = True
            self._model.enqueue(lambda: self._model.cc_status.set(devices))
            _FlushQueue(
                self._model
            ).run()  # Ensure the queue is serviced before returning


class DisableChromecast(Scenario):
    """Disable a random Chromecast device."""

    def __init__(self, model: Model) -> None:
        """Disable a random Chromecast device.

        :param model: the application model
        """
        super().__init__()
        self._model = model

    def run(self) -> None:
        """Disable a random Chromecast device."""
        devices = self._model.cc_status.get()
        enabled_devices = list(filter(lambda d: d.enabled, devices))
        if len(enabled_devices) > 0:
            device = random.choice(enabled_devices)
            logger.info("Disabling chromecast %s", device.name)
            for dev in devices:
                if dev.name == device.name:
                    dev.enabled = False
            self._model.enqueue(lambda: self._model.cc_status.set(devices))
            _FlushQueue(
                self._model
            ).run()  # Ensure the queue is serviced before returning


class ToggleChromecast(Scenario):
    """Toggle a random Chromecast device."""

    def __init__(self, model: Model) -> None:
        """Toggle a random Chromecast device.

        :param model: the application model
        """
        super().__init__()
        self._model = model

    def run(self) -> None:
        """Toggle a random Chromecast device."""
        devices = self._model.cc_status.get().copy()
        if len(devices) > 0:
            device = random.choice(devices)
            logger.info(
                "Toggling chromecast %s - %s -> %s",
                device.name,
                device.enabled,
                not device.enabled,
            )
            device.enabled = not device.enabled
            self._model.enqueue(lambda: self._model.cc_status.set(devices))
            _FlushQueue(
                self._model
            ).run()  # Ensure the queue is serviced before returning


class _FlushQueue(Scenario):
    """Flush the model's event queue."""

    def __init__(self, model: Model) -> None:
        """Flush the model's event queue.

        :param model: the application model
        """
        super().__init__()
        self._model = model
        self._flushed = False

    def run(self) -> None:
        """Flush the queue."""

        def _set_flushed() -> None:
            logger.debug("Queue serviced: id=%d", id(self))
            self._flushed = True

        self._model.enqueue(_set_flushed)
        logger.debug("Waiting for event queue to be serviced: id=%d", id(self))
        assert eventually(lambda: self._flushed, 0.1, 100), "Ensure queue is serviced"
