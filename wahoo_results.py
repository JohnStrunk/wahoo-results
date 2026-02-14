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
import sys
import threading
import webbrowser
from pathlib import PurePath
from time import sleep
from tkinter import Tk, filedialog, messagebox

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
import imagecast_types
import main_window
import raceinfo
import wh_analytics
import wh_version
from about import about
from model import Model
from raceinfo import ColoradoSCB, DolphinEvent, Heat, Time
from raceinfo.timingsystem import TimingSystem
from resolver import standard_resolver
from scoreboard import ScoreboardImage, waiting_screen
from scoreboard_window import make_sb_window
from template import get_template
from version import SENTRY_DSN, WAHOO_RESULTS_VERSION
from watcher import ResultWatcher, SCBWatcher

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
            messagebox.showerror(  # type: ignore
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
        template = ScoreboardImage(
            imagecast_types.IMAGE_SIZE, get_template(), model, True
        )
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
        preview = ScoreboardImage(imagecast_types.IMAGE_SIZE, get_template(), model)
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
        model.dq_mode,
    ]:
        element.trace_add("write", lambda var, idx, op: update_preview())
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


def setup_ext_scoreboard(model: Model) -> None:
    """Set up the external scoreboard functionality.

    :param model: The application model
    """

    def ensure_sb_window() -> None:
        if (
            model.scoreboard_window is not None
            and model.scoreboard_window.winfo_exists()
        ):
            model.scoreboard_window.destroy()
            model.scoreboard_window = None
        else:
            model.scoreboard_window = make_sb_window(model.root, model.scoreboard)

    model.show_scoreboard_window.add(ensure_sb_window)


def setup_clear_scoreboard(model: Model) -> None:
    """Set up the handler for clearing the scoreboard.

    :param model: The application model
    """

    def clear_scoreboard() -> None:
        """Clear the scoreboard image."""
        model.scoreboard.set(waiting_screen(imagecast_types.IMAGE_SIZE, model))
        model.latest_result.set(None)

    model.clear_scoreboard.add(clear_scoreboard)


def setup_scb_watcher(model: Model, observer: BaseObserver) -> None:
    """Set up handlers for when new scb files are detected.

    :param model: The application model
    :param observer: The file system observer
    """

    def process_startlists() -> None:
        """Load all the startlists from the current directory and update the UI with their information."""
        directory = model.dir_startlist.get()
        startlists = ColoradoSCB().full_program(directory)
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

    model.dir_startlist.trace_add("write", lambda var, idx, op: scb_dir_updated())
    scb_dir_updated()


def summarize_racedir(directory: str, timing_system: TimingSystem) -> list[Heat]:
    """Summarize all race results in a directory.

    :param directory: The directory to process
    :param timing_system: The timing system to use for reading results
    :returns: A list of HeatData objects
    """
    files = os.scandir(directory)
    contents: list[Heat] = []
    for file in files:
        if any(PurePath(file).match(pattern) for pattern in timing_system.patterns):
            try:
                result = timing_system.read(file.path)
                contents.append(result)
            except ValueError:
                pass
            except OSError:
                pass
    return contents


def load_result(
    timing_system: TimingSystem,
    startlist_dir: str,
    min_times: int,
    time_threshold: float,
    filename: str,
) -> Heat | None:
    """Load a result file and corresponding startlist.

    :param timing_system: The timing system to use
    :param startlist_dir: The directory containing startlists
    :param min_times: Minimum number of times required
    :param time_threshold: Threshold for time validity
    :param filename: The result file to load
    :returns: The HeatData object representing the result if successful,
        otherwise None
    """
    result: Heat | None = None
    resolver = standard_resolver(min_times, Time(str(time_threshold)))
    # still being written.
    for tries in range(1, 6):
        try:
            result = timing_system.read(filename)
            result.resolve_times(resolver)
            break
        except ValueError:
            sleep(0.05 * tries)
        except OSError:
            sleep(0.05 * tries)
    if result is None:
        return None
    if result.event is None or result.heat is None:
        return None
    try:
        heatinfo = ColoradoSCB().find(startlist_dir, result.event, result.heat)
        result.merge(info_from=heatinfo)
    except OSError:
        pass
    except ValueError:
        pass
    return result


def setup_result_watcher(model: Model, observer: BaseObserver) -> None:
    """Set up watches for files/directories and connect to model.

    :param model: The application model
    :param observer: The watcher for result files
    """

    def update_timing_system() -> None:
        format = model.result_format.get()
        system = raceinfo.timing_systems.get(format)
        if system is not None:
            model.timing_system = system()

    def process_racedir() -> None:
        """Load all the race resultsand update the UI."""
        # Capture variables on the main thread
        directory = model.dir_results.get()
        timing_system = model.timing_system

        def _bg_process_racedir() -> None:
            with sentry_sdk.start_span(
                op="update_race_ui", description="Update race summaries in UI"
            ) as span:
                contents = summarize_racedir(directory, timing_system)
                span.set_tag("race_files", len(contents))
                model.enqueue(lambda: model.results_contents.set(contents))

        threading.Thread(target=_bg_process_racedir, daemon=True).start()

    def process_new_result(file: str) -> None:
        """Process a new race result that has been detected.

        :param file: The new result file to process
        """
        # Capture variables on the main thread
        timing_system = model.timing_system
        startlist_dir = model.dir_startlist.get()
        min_times = model.min_times.get()
        time_threshold = model.time_threshold.get()
        autosave_enabled = model.autosave_scoreboard.get()
        dir_autosave = model.dir_autosave.get()
        # Num active chromecasts for analytics
        num_cc = len([x for x in model.cc_status.get() if x.enabled])

        def _bg_process_new_result() -> None:
            with sentry_sdk.start_transaction(op="new_result", name="New race result"):
                result = load_result(
                    timing_system, startlist_dir, min_times, time_threshold, file
                )
                if result is None:
                    return

                def _ui_update() -> None:
                    scoreboard = ScoreboardImage(
                        imagecast_types.IMAGE_SIZE, result, model
                    )
                    model.scoreboard.set(scoreboard.image)
                    model.latest_result.set(result)

                    if autosave_enabled:

                        def _bg_save() -> None:
                            try:
                                if not os.path.exists(dir_autosave):
                                    os.makedirs(dir_autosave)
                                filename = f"E{int(result.event or 0):03d}-H{int(result.heat or 0):02d}-scoreboard.png"
                                filepath = os.path.join(dir_autosave, filename)
                                scoreboard.image.save(filepath)
                            except (OSError, IOError) as e:
                                logger.error(
                                    "Error autosaving scoreboard to %s: %s",
                                    dir_autosave,
                                    e,
                                )
                                model.enqueue(
                                    lambda e=e: messagebox.showerror(  # type: ignore
                                        "Autosave Error",
                                        f"Could not save scoreboard image to '{dir_autosave}':\n{e}",
                                    )
                                )

                        threading.Thread(target=_bg_save, daemon=True).start()

                    wh_analytics.results_received(result.has_names(), num_cc)
                    process_racedir()  # update the UI

                model.enqueue(_ui_update)

        threading.Thread(target=_bg_process_new_result, daemon=True).start()

    def result_dir_updated() -> None:
        """When the raceresult directory is changed, update the watch to look at the new directory and trigger processing of the results."""
        path = model.dir_results.get()
        if not os.path.exists(path):
            return
        observer.unschedule_all()
        update_timing_system()

        def async_process(file: str) -> None:
            model.enqueue(lambda: process_new_result(file))

        observer.schedule(ResultWatcher(async_process, model.timing_system), path)
        logger.debug("result watcher updated to %s", path)
        process_racedir()

    # Need to update the result dir both when the directory changes and when the
    # result format changes, since the format is used to determine the timing
    # system
    model.dir_results.trace_add("write", lambda var, idx, op: result_dir_updated())
    model.result_format.trace_add("write", lambda var, idx, op: result_dir_updated())
    result_dir_updated()


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
            model.statusclick.add(
                lambda: (webbrowser.open(latest_version.url), None)[1]
            )
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

    model.cc_status.trace_add("write", lambda var, idx, op: update_cc_list())
    icast.set_discovery_callback(cast_discovery)

    # Link Chromecast contents to the UI preview
    model.scoreboard.trace_add(
        "write", lambda var, idx, op: icast.publish(model.scoreboard.get())
    )


def initialize_sentry(model: Model) -> None:
    """Initialize sentry.io crash reporting.

    :param model: The application model
    """
    execution_environment = "source"
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        execution_environment = "executable"
    if autotest.testing:
        execution_environment = "test"

    # Initialize Sentry crash reporting
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        sample_rate=1.0,
        traces_sample_rate=0.3 if execution_environment == "executable" else 0,
        environment=execution_environment,
        release=f"wahoo-results@{WAHOO_RESULTS_VERSION}",
        include_local_variables=True,
        send_default_pii=True,
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

    screen_size = (root.winfo_screenwidth(), root.winfo_screenheight())
    wh_analytics.application_start(
        analytics_enabled=model.analytics.get(),
        client_id=model.client_id.get(),
        screen_size=screen_size,
    )
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

    result_observer = Observer()
    result_observer.start()
    setup_result_watcher(model, result_observer)

    def write_dolphin_csv():
        try:
            directory = model.dir_startlist.get()
            program = ColoradoSCB().full_program(directory)
            filename = os.path.join(directory, "dolphin_events.csv")
            DolphinEvent().write(filename, program)
            wh_analytics.wrote_dolphin_csv(len(program.keys()))
        except OSError:
            pass

    model.dolphin_export.add(write_dolphin_csv)

    # Connections for the run tab
    icast = imagecast.ImageCast(9998)
    setup_run(model, icast)
    icast.start()

    # Set initial scoreboard image
    model.scoreboard.set(waiting_screen(imagecast_types.IMAGE_SIZE, model))
    setup_ext_scoreboard(model)
    setup_clear_scoreboard(model)

    # Analytics triggers
    model.menu_docs.add(wh_analytics.documentation_link)
    model.statusclick.add(wh_analytics.update_link)
    model.dir_startlist.trace_add(
        "write", lambda var, idx, op: wh_analytics.set_cts_directory(True)
    )
    model.dir_results.trace_add(
        "write", lambda var, idx, op: wh_analytics.set_result_directory(True)
    )

    # Allow the root window to build, then close the splash screen if it's up
    # and we're running in exe mode
    try:
        root.update()
        import pyi_splash  # noqa: PLC0415 # type: ignore

        if pyi_splash.is_alive():
            pyi_splash.close()
    except ModuleNotFoundError:
        pass
    except RuntimeError:
        pass

    root.resizable(True, True)  # Allow resizing of the main window

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
    result_observer.unschedule_all()
    result_observer.stop()
    # result_observer.join()  # This causes an intermittent hang
    logger.debug("Watchers stopped")
    icast.stop()
    root.update()
    wh_analytics.application_stop(
        num_lanes=model.num_lanes.get(),
        has_bg_image=(model.image_bg.get() != ""),
        dq_mode=model.dq_mode.get(),
        result_format=model.result_format.get(),
        time_threshold=model.time_threshold.get(),
        min_times=model.min_times.get(),
        normal_font=model.font_normal.get(),
        time_font=model.font_time.get(),
    )
    root.update()

    # Sentry v2 has deprecated Hub, so we can't manually close the client
    # logger.debug("Shutting down Sentry")
    # client = sentry_sdk.Hub.current.client
    # if client is not None:
    #     client.close(timeout=2.0)
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
