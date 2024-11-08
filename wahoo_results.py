#! /usr/bin/env python
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

"""Wahoo Results!"""  # noqa: D400

import argparse
import copy
import logging
import os
import platform
import re
import sys
import threading
import webbrowser
from time import sleep
from tkinter import Tk, filedialog, messagebox
from typing import List, Optional

import sentry_sdk
from requests.exceptions import RequestException
from sentry_sdk.integrations.socket import SocketIntegration
from sentry_sdk.integrations.threading import ThreadingIntegration
from watchdog.observers import Observer

# We can't use Observer in type specifications due to
# https://github.com/gorakhargosh/watchdog/issues/982 but we can use
# BaseObserver as a workaround
from watchdog.observers.api import BaseObserver

import autotest
import imagecast
import main_window
import wh_analytics
import wh_version
from about import about
from model import Model
from raceinfo import (
    HeatData,
    NumericTime,
    load_all_scb,
    parse_do4_file,
    parse_scb_file,
    standard_resolver,
    startlists_to_csv,
)
from scoreboard import ScoreboardImage, waiting_screen
from template import get_template
from version import SENTRY_DSN, WAHOO_RESULTS_VERSION
from watcher import DO4Watcher, SCBWatcher

CONFIG_FILE = "wahoo-results.ini"
logger = logging.getLogger(__name__)


def setup_exit(root: Tk, model: Model) -> None:
    """Set up handlers for application exit.

    :param root: The Tk root window
    :param model: The application model
    """

    def exit_fn() -> None:
        """Exit the application."""
        logger.info("Exit called")
        try:
            model.save(CONFIG_FILE)
        except PermissionError as err:
            logger.debug("Error saving configuration")
            messagebox.showerror(
                title="Error saving configuration",
                message=f'Unable to write configuration file "{err.filename}". {err.strerror}',
                detail="Please ensure the working directory is writable.",
            )
        logger.debug("Exiting main loop")
        root.quit()  # Exit mainloop

    # Close box exits app
    root.protocol("WM_DELETE_WINDOW", exit_fn)
    # Exit menu item exits app
    model.menu_exit.add(exit_fn)


def setup_template(model: Model) -> None:
    """Set up handler for exporting scoreboard template.

    :param model: The application model
    """

    def do_export() -> None:
        """Export the current template to a file."""
        filename = filedialog.asksaveasfilename(
            confirmoverwrite=True,
            defaultextension=".png",
            filetypes=[("image", "*.png")],
            initialfile="template",
        )
        if len(filename) == 0:
            return
        template = ScoreboardImage(imagecast.IMAGE_SIZE, get_template(), model, True)
        template.image.save(filename)

    model.menu_export_template.add(do_export)


def setup_save(model: Model) -> None:
    """Set up handler for saving current scoreboard image."""

    def do_save() -> None:
        """Save the current scoreboard image to a file."""
        filename = filedialog.asksaveasfilename(
            confirmoverwrite=True,
            defaultextension=".png",
            filetypes=[("image", "*.png")],
            initialfile="scoreboard",
        )
        if len(filename) == 0:
            return
        sb_image = model.scoreboard.get()
        sb_image.save(filename)

    model.menu_save_scoreboard.add(do_save)


def setup_appearance(model: Model) -> None:
    """Link model changes to the scoreboard preview.

    When one of the model variables that affect the appearance of the scoreboard
    changes, update the preview.

    :param model: The application model
    """

    def update_preview() -> None:
        """Update the appearance preview with the current settings."""
        preview = ScoreboardImage(imagecast.IMAGE_SIZE, get_template(), model)
        model.appearance_preview.set(preview.image)

    for element in [
        model.font_normal,
        model.font_time,
        model.text_spacing,
        model.title,
        model.image_bg,
        model.color_title,
        model.color_event,
        model.color_even,
        model.color_odd,
        model.color_first,
        model.color_second,
        model.color_third,
        model.color_bg,
        model.brightness_bg,
        model.num_lanes,
    ]:
        element.trace_add("write", lambda *_: update_preview())
    update_preview()

    def handle_bg_import() -> None:
        """Import a background image."""
        image = filedialog.askopenfilename(
            filetypes=[("image", "*.gif *.jpg *.jpeg *.png")]
        )
        if len(image) == 0:
            return
        image = os.path.normpath(image)
        model.image_bg.set(image)

    model.bg_import.add(handle_bg_import)
    model.bg_clear.add(lambda: model.image_bg.set(""))


def setup_scb_watcher(model: Model, observer: BaseObserver) -> None:
    """Set up handlers for when new scb files are detected.

    :param model: The application model
    :param observer: The file system observer
    """

    def process_startlists() -> None:
        """Load all the startlists from the current directory and update the UI with their information."""
        directory = model.dir_startlist.get()
        startlists = load_all_scb(directory)
        model.startlist_contents.set(startlists)

    def scb_dir_updated() -> None:
        """When the startlist directory is changed, update the watched to look at the new directory and trigger processing of the startlists."""
        path = model.dir_startlist.get()
        if not os.path.exists(path):
            return
        observer.unschedule_all()
        # When the watcher notices a change in the startlists, the update
        # needs to happen from the main thread, so we enqueue instead of
        # directly call process_startlists from the SCBWatcher.
        observer.schedule(SCBWatcher(lambda: model.enqueue(process_startlists)), path)
        logger.debug("scb watcher updated to %s", path)
        process_startlists()

    model.dir_startlist.trace_add("write", lambda *_: scb_dir_updated())
    scb_dir_updated()


def summarize_racedir(directory: str) -> List[HeatData]:
    """Summarize all race results in a directory.

    :param directory: The directory to process
    :returns: A list of HeatData objects
    """
    files = os.scandir(directory)
    contents: List[HeatData] = []
    for file in files:
        if file.name.endswith(".do4"):
            match = re.match(r"^(\d+)-", file.name)
            if match is None:
                continue
            try:
                result = parse_do4_file(file.path)
                contents.append(result)
            except ValueError:
                pass
            except OSError:
                pass
    return contents


def load_result(model: Model, filename: str) -> Optional[HeatData]:
    """Load a result file and corresponding startlist.

    :param model: The application model
    :param filename: The .do4 result file to load
    :returns: The HeatData object representing the result if successful,
        otherwise None
    """
    result: Optional[HeatData] = None
    # Retry mechanism since we get errors if we try to read while it's
    # still being written.
    for tries in range(1, 6):
        try:
            result = parse_do4_file(filename)
            result.resolver = standard_resolver(
                model.min_times.get(), NumericTime(model.time_threshold.get())
            )
            break
        except ValueError:
            sleep(0.05 * tries)
        except OSError:
            sleep(0.05 * tries)
    if result is None:
        return None
    efilename = f"E{result.event:0>3}.scb"
    try:
        startlist = parse_scb_file(os.path.join(model.dir_startlist.get(), efilename))
        if len(startlist) >= result.heat:
            result.merge(info_from=startlist[result.heat - 1])
    except OSError:
        pass
    except ValueError:
        pass
    return result


def setup_do4_watcher(model: Model, observer: BaseObserver) -> None:
    """Set up watches for files/directories and connect to model.

    :param model: The application model
    :param observer: The watcher for do4 files
    """

    def process_racedir() -> None:
        """Load all the race resultsand update the UI."""
        with sentry_sdk.start_span(
            op="update_race_ui", description="Update race summaries in UI"
        ) as span:
            directory = model.dir_results.get()
            contents = summarize_racedir(directory)
            span.set_tag("race_files", len(contents))
            model.results_contents.set(contents)

    def process_new_result(file: str) -> None:
        """Process a new race result that has been detected.

        :param file: The new result file to process
        """
        with sentry_sdk.start_transaction(op="new_result", name="New race result"):
            result = load_result(model, file)
            if result is None:
                return
            scoreboard = ScoreboardImage(imagecast.IMAGE_SIZE, result, model)
            model.scoreboard.set(scoreboard.image)
            model.latest_result.set(result)
            num_cc = len([x for x in model.cc_status.get() if x.enabled])
            wh_analytics.results_received(result.has_names(), num_cc)
            process_racedir()  # update the UI

    def do4_dir_updated() -> None:
        """When the raceresult directory is changed, update the watch to look at the new directory and trigger processing of the results."""
        path = model.dir_results.get()
        if not os.path.exists(path):
            return
        observer.unschedule_all()

        def async_process(file: str) -> None:
            model.enqueue(lambda: process_new_result(file))

        observer.schedule(DO4Watcher(async_process), path)
        logger.debug("do4 watcher updated to %s", path)
        process_racedir()

    model.dir_results.trace_add("write", lambda *_: do4_dir_updated())
    do4_dir_updated()


def check_for_update(model: Model) -> None:
    """Notify the user if there's a newer released version of Wahoo Results.

    :param model: The application model
    """
    current_version = model.version.get()
    try:
        latest_version = wh_version.latest()
        if latest_version is not None and not wh_version.is_latest_version(
            latest_version, current_version
        ):
            model.statustext.set(
                f"New version available. Click to download: {latest_version.tag}"
            )
            model.statusclick.add(lambda: webbrowser.open(latest_version.url))
    except RequestException as ex:
        logger.warning("Error checking for update: %s", ex)


def setup_run(model: Model, icast: imagecast.ImageCast) -> None:
    """Link Chromecast discovery/management to the UI.

    :param model: The application model
    :param icast: The ImageCast object that manages Chromecast connections
    """

    def cast_discovery() -> None:
        """Update the list of Chromecasts in the model when the discovered device list changes."""
        dev_list = copy.deepcopy(icast.get_devices())
        model.enqueue(lambda: model.cc_status.set(dev_list))

    def update_cc_list() -> None:
        """Notify the ImageCast object when a device should be en/dis-abled."""
        dev_list = model.cc_status.get()
        for dev in dev_list:
            icast.enable(dev.uuid, dev.enabled)

    model.cc_status.trace_add("write", lambda *_: update_cc_list())
    icast.set_discovery_callback(cast_discovery)

    # Link Chromecast contents to the UI preview
    model.scoreboard.trace_add(
        "write", lambda *_: icast.publish(model.scoreboard.get())
    )


def initialize_sentry(model: Model) -> None:
    """Initialize sentry.io crash reporting.

    :param model: The application model
    """
    execution_environment = "source"
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        execution_environment = "executable"
    if autotest.TESTING:
        execution_environment = "test"

    # Initialize Sentry crash reporting
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        sample_rate=1.0,
        traces_sample_rate=0.3 if execution_environment == "executable" else 0,
        environment=execution_environment,
        release=f"wahoo-results@{WAHOO_RESULTS_VERSION}",
        include_local_variables=True,
        integrations=[SocketIntegration(), ThreadingIntegration(propagate_hub=True)],
        debug=False,
    )
    uname = platform.uname()
    sentry_sdk.set_tag("os_system", uname.system)
    sentry_sdk.set_tag("os_release", uname.release)
    sentry_sdk.set_tag("os_version", uname.version)
    sentry_sdk.set_tag("os_machine", uname.machine)
    sentry_sdk.set_user(
        {
            "id": model.client_id.get(),
            "ip_address": "{{auto}}",
        }
    )


def main() -> None:  # noqa: PLR0915
    """Run the main program."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "--loglevel",
        type=str,
        help="Set the log level",
        choices=["debug", "info", "warning", "error", "critical"],
    )
    arg_parser.add_argument(
        "--logfile",
        type=str,
        help="Send log output to the specified file instead of the screen",
    )
    arg_parser.add_argument(
        "--test",
        type=str,
        help="Enable test mode, running for the specified scenario",
    )
    args = arg_parser.parse_args()
    if args.loglevel is not None:
        loglevel = args.loglevel
        numeric_level = getattr(logging, loglevel.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f"Invalid log level: {loglevel}")
        logging.basicConfig(
            format="%(asctime)s %(module)s %(levelname)s %(message)s",
            level=numeric_level,
            filename=args.logfile,  # May be None
        )
    if args.test is not None:
        autotest.set_test_mode()

    root = Tk()

    model = Model(root)

    model.load(CONFIG_FILE)
    model.version.set(WAHOO_RESULTS_VERSION)

    initialize_sentry(model)
    hub = sentry_sdk.Hub.current
    hub.start_session(session_mode="application")

    screen_size = (root.winfo_screenwidth(), root.winfo_screenheight())
    wh_analytics.application_start(model, screen_size)
    sentry_sdk.set_context(
        "display",
        {
            "size": f"{screen_size[0]}x{screen_size[1]}",
        },
    )

    main_window.View(root, model)

    setup_exit(root, model)
    setup_save(model)
    setup_template(model)

    def docs_fn() -> None:
        query_params = "&".join(
            [
                "utm_source=wahoo_results",
                "utm_medium=menu",
                "utm_campaign=docs_link",
                f"ajs_uid={model.client_id.get()}",
            ]
        )
        webbrowser.open("https://wahoo-results.com/?" + query_params)

    model.menu_docs.add(docs_fn)
    check_for_update(model)

    model.menu_about.add(lambda: about(root))

    # Connections for the appearance tab
    setup_appearance(model)

    # Connections for the directories tab
    scb_observer = Observer()
    scb_observer.start()
    setup_scb_watcher(model, scb_observer)

    do4_observer = Observer()
    do4_observer.start()
    setup_do4_watcher(model, do4_observer)

    def write_dolphin_csv():
        directory = model.dir_startlist.get()
        slists = load_all_scb(directory)
        csv = startlists_to_csv(slists)
        filename = os.path.join(directory, "dolphin_events.csv")
        with open(filename, "w", encoding="cp1252") as file:
            file.writelines(csv)
        num_events = len(csv)
        wh_analytics.wrote_dolphin_csv(num_events)

    model.dolphin_export.add(write_dolphin_csv)

    # Connections for the run tab
    icast = imagecast.ImageCast(9998)
    setup_run(model, icast)
    icast.start()

    # Set initial scoreboard image
    model.scoreboard.set(waiting_screen(imagecast.IMAGE_SIZE, model))

    # Analytics triggers
    model.menu_docs.add(wh_analytics.documentation_link)
    model.statusclick.add(wh_analytics.update_link)
    model.dir_startlist.trace_add(
        "write", lambda *_: wh_analytics.set_cts_directory(True)
    )
    model.dir_results.trace_add(
        "write", lambda *_: wh_analytics.set_do4_directory(True)
    )

    # Allow the root window to build, then close the splash screen if it's up
    # and we're running in exe mode
    try:
        root.update()
        import pyi_splash  # type: ignore

        if pyi_splash.is_alive():
            pyi_splash.close()
    except ModuleNotFoundError:
        pass
    except RuntimeError:
        pass

    if args.test is not None:
        scenario = autotest.build_scenario(model, args.test)
        autotest.run_scenario(scenario)

    root.mainloop()
    logger.debug("Cancelling all 'after' events")
    for after_id in root.tk.eval("after info").split():
        root.after_cancel(after_id)

    root.update()

    logger.debug("Stopping watchers")
    scb_observer.unschedule_all()
    scb_observer.stop()
    # scb_observer.join()  # This causes an intermittent hang
    do4_observer.unschedule_all()
    do4_observer.stop()
    # do4_observer.join()  # This causes an intermittent hang
    logger.debug("Watchers stopped")
    icast.stop()
    root.update()
    wh_analytics.application_stop(model)
    root.update()
    logger.debug("Shutting down Sentry")
    hub.end_session()
    client = hub.client
    if client is not None:
        client.close(timeout=2.0)
    if logger.isEnabledFor(logging.DEBUG):
        for thread in threading.enumerate():
            logger.debug(
                "Thread %s - alive: %s, daemon: %s",
                thread.name,
                thread.is_alive(),
                thread.daemon,
            )


if __name__ == "__main__":
    main()
