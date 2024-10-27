# Wahoo! Results - https://github.com/JohnStrunk/wahoo-results
# Copyright (C) 2021 - John D. Strunk
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

"""
This file provides the ImageCast class that can be used to publish static PNG
images to Chromecast devices. It abstracts the interactions with the Chromecast
devices by managing connections and providing an integrated web server.
"""

import logging
import threading
import time
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID

import pychromecast  # type: ignore
import sentry_sdk
import zeroconf
from PIL import Image  # type: ignore
from pychromecast.controllers.media import BaseMediaPlayer  # type: ignore
from pychromecast.error import NotConnected  # type: ignore

# Resolution of images for the Chromecast
IMAGE_SIZE = (1280, 720)

# Chromecast image refresh interval (seconds)
# Newer versions of the Chromecast firmware seem to have a 10 minute timeout
_REFRESH_INTERVAL = 7 * 60

# Chomecast application id
_WAHOO_RESULTS_APP_ID = "34B218B6"

logger = logging.getLogger(__name__)


@dataclass
class DeviceStatus:
    """The status of a Chromecast device"""

    uuid: UUID  # UUID for the device
    name: str  # Friendly name for the device
    enabled: bool  # Whether the device is enabled


DiscoveryCallbackFn = Callable[[], None]


class ICController(BaseMediaPlayer):
    """Media controller for ImageCast"""

    def __init__(self):
        super().__init__(_WAHOO_RESULTS_APP_ID)

    def send_image(self, url: str, mime_type: str):
        """Send an image to the Chromecast"""
        logger.debug("Sending image via quick_play to Chromecast: %s", url)
        super().quick_play(
            media_id=url,
            media_type=mime_type,
            timeout=30.0,
            metadata={"metadataType": 0, "title": ""},
        )
        logger.debug("quick_play done")


class ImageCast:
    """
    The ImageCast class encapsulates everything necessary to cast images to a
    set of Chromecast devices.
    """

    _server_port: int  # port for the web server
    # _devices maps the chromecast uuid to a map of:
    #    "cast" -> its chromecast object
    #    "enabled" -> boolean indicating whether we should cast to this device
    devices: Dict[UUID, Dict[str, Any]]
    _webserver_thread: Optional[threading.Thread]
    _refresh_thread: Optional[threading.Thread]
    image: Optional[Image.Image]
    callback_fn: Optional[DiscoveryCallbackFn]
    browser: Optional[pychromecast.CastBrowser]
    zconf: Optional[zeroconf.Zeroconf]

    def __init__(self, server_port: int) -> None:
        """
        Create an instance to communicate with a set of Chromecast devices.

        Parameters:
            - server_port: The port on the local machine that will host the
              embedded web server for the Chromecast(s) to connect to.
        """
        self._server_port = server_port
        self.devices = {}
        self.image = None
        self.callback_fn = None
        self._webserver_thread = None
        self._refresh_thread = None
        self.zconf = None
        self.browser = None

    def start(self):
        """
        Start the background processes. This must be called before publishing
        images.
        """
        self._start_webserver()
        self._start_listener()
        self._start_refresh()

    def stop(self) -> None:
        """
        Shut down the background processes and disconnect from the
        Chromecast(s).
        """
        logger.debug("Stopping ImageCast and disconnecting from Chromecasts")
        # Separate generating the list from disconnecting becase disconnecting
        # can alter the list
        to_disconnect: list[pychromecast.Chromecast] = []
        for state in self.devices.values():
            if state["enabled"]:
                to_disconnect.append(state["cast"])
        for cast in to_disconnect:
            self._disconnect(cast)
        if self.browser is not None:
            self.browser.stop_discovery()
        if self.zconf is not None:
            self.zconf.close()

    @classmethod
    def _disconnect(cls, cast: pychromecast.Chromecast) -> None:
        with sentry_sdk.start_span(op="disconnect"):
            logger.debug("Disconnecting from %s", cast.name)
            try:
                cast.quit_app()
            except NotConnected:
                pass

    def set_discovery_callback(self, func: DiscoveryCallbackFn) -> None:
        """
        Sets the callback function that will be called when the list of
        discovered Chromecasts changes.
        """
        self.callback_fn = func

    def enable(self, uuid: UUID, enabled: bool) -> None:
        """
        Set whether to include or exclude a specific Chromecast device from
        receiving the published images.
        """
        with sentry_sdk.start_transaction(
            op="enable_cc", name="Enable/disable Chromecast"
        ):
            if self.devices[uuid] is not None:
                previous = self.devices[uuid]["enabled"]
                self.devices[uuid]["enabled"] = enabled
                if enabled and not previous:  # enabling: send the latest image
                    logger.debug("Enabling %s", self.devices[uuid]["cast"].name)
                    self._publish_one(self.devices[uuid]["cast"])
                elif previous and not enabled:  # disabling: disconnect
                    logger.debug("Disabling %s", self.devices[uuid]["cast"].name)
                    self._disconnect(self.devices[uuid]["cast"])

    def get_devices(self) -> List[DeviceStatus]:
        """
        Get the current list of known Chromecast devices and whether they are
        currently enabled.
        """
        devs: List[DeviceStatus] = []
        for uuid, state in self.devices.items():
            devs.append(
                DeviceStatus(
                    uuid, state["cast"].cast_info.friendly_name, state["enabled"]
                )
            )
        return devs

    def publish(self, image: Image.Image) -> None:
        """
        Publish a new image to the currently enabled Chromecast devices.
        """
        with sentry_sdk.start_transaction(
            op="publish_image", name="Publish image"
        ) as txn:
            num = len([x for x in self.devices.values() if x["enabled"]])
            txn.set_tag("enabled_cc", num)
            self.image = image
            for state in self.devices.values():
                if state["enabled"]:
                    self._publish_one(state["cast"])

    def _publish_one(self, cast: pychromecast.Chromecast) -> None:
        with sentry_sdk.start_span(op="publish_one"):
            if self.image is None:
                return
            # Use the local address of the socket to handle environments with
            # multiple NICs and cases where the host IP changes.
            sock = cast.socket_client.socket
            if sock is None:
                return
            try:
                local_addr = sock.getsockname()[0]
            except OSError:  # Socket is closed or not connected. Nothing to do.
                return
            # Use the current time as the URL to force the CC to refresh the image
            sec = int(time.time())
            url = f"http://{local_addr}:{self._server_port}/image-{sec}.png"
            # Set media controller to use our app
            controller = ICController()
            logger.debug("Setting controller for %s", cast.name)
            cast.register_handler(controller)
            logger.debug("Publishing to %s", cast.name)
            try:
                controller.send_image(url, "image/png")
            except NotConnected:
                logger.debug("Error: NotConnected while publishing to %s", cast.name)
            except pychromecast.PyChromecastError:
                logger.debug(
                    "Error: PyChromecastError while publishing to %s", cast.name
                )
            finally:
                logger.debug("Unregistering controller for %s", cast.name)
                cast.unregister_handler(controller)

    def _start_webserver(self) -> None:
        parent = self

        class WSHandler(BaseHTTPRequestHandler):
            """Handle web requests coming from the CCs"""

            def do_GET(self):
                """Respond to CC w/ the current image"""
                with sentry_sdk.start_transaction(op="http", name="GET"):
                    self.send_response(200)
                    self.send_header("Content-type", "image/png")
                    self.end_headers()
                    if parent.image is not None:
                        parent.image.save(self.wfile, "PNG", optimize=True)

            def log_message(self, format, *args):
                logger.debug(format, *args)

        def _webserver_run():
            web_server = HTTPServer(("", self._server_port), WSHandler)
            web_server.serve_forever()

        self._webserver_thread = threading.Thread(target=_webserver_run, daemon=True)
        self._webserver_thread.start()

    # The refresh thread periodically re-publishes the current image to ensure
    # the Chromecast devices don't timeout.
    def _start_refresh(self) -> None:
        def _refresh_run():
            while True:
                time.sleep(_REFRESH_INTERVAL)
                if self.image is not None:
                    self.publish(self.image)

        self._refresh_thread = threading.Thread(target=_refresh_run, daemon=True)
        self._refresh_thread.start()

    # The listener thread handles discovery of new Chromecast devices and
    # adds/removes them from the device list.
    def _start_listener(self) -> None:
        parent = self

        class Listener(pychromecast.discovery.AbstractCastListener):
            """Receive chromecast discovery updates"""

            def add_cast(self, uuid: UUID, service: str):
                logger.debug("Got add cast: %s", str(uuid))
                self.update_cast(uuid, service)
                # We don't trigger the callback here because update_cast will do
                # it for us.

            def remove_cast(
                self, uuid: UUID, service: str, cast_info: pychromecast.CastInfo
            ):
                logger.debug("Got remove cast: %s", str(uuid))
                try:
                    del parent.devices[uuid]
                except KeyError:
                    # received a removal message for a CC we weren't tracking.
                    # Ignore it.
                    pass
                if parent.callback_fn is not None:
                    parent.callback_fn()

            def update_cast(self, uuid: UUID, service: str) -> None:
                with sentry_sdk.start_transaction(
                    op="cc_update", name="Chromecast update recieved"
                ):
                    logger.debug("Got update cast: %s", str(uuid))
                    if uuid not in parent.devices:  # new device
                        if parent.browser is None:
                            return
                        svcs = parent.browser.services
                        cast = pychromecast.get_chromecast_from_cast_info(
                            svcs[uuid], parent.zconf
                        )
                        cast.wait(timeout=2)
                        # We only care about devices that we can cast to (i.e., not
                        # audio devices)
                        if (
                            cast.cast_info.cast_type
                            != pychromecast.CAST_TYPE_CHROMECAST
                        ):
                            logger.debug("Not cast-able. Ignoring: %s", cast.name)
                            try:
                                cast.disconnect(timeout=0)  # don't block
                            except TimeoutError:
                                pass  # Since we're not blocking, this is expected
                            return
                        logger.debug("Adding to device list: %s", cast.name)
                        parent.devices[uuid] = {"cast": cast, "enabled": False}
                    if parent.callback_fn is not None:
                        logger.debug(
                            "Triggering callback for: %s",
                            parent.devices[uuid]["cast"].name,
                        )
                        parent.callback_fn()

        self.zconf = zeroconf.Zeroconf()
        self.browser = pychromecast.discovery.CastBrowser(Listener(), self.zconf)
        self.browser.start_discovery()


def _main():
    """Simple test of the ImageCast class."""
    image = Image.open("file.png")

    # Simple callback when CC device status changes. We just print what's
    # currently known and make sure all the discovered devices are enabled.
    def callback():
        status = imgcast.get_devices()
        for device in status:
            print(f"{device.name} -> {device.enabled}")
            imgcast.enable(device.uuid, True)
        print("---")

    imgcast = ImageCast(9657)
    imgcast.set_discovery_callback(callback)
    imgcast.start()
    iterations = 3
    for i in range(0, iterations):
        print(f"Publishing iteration: {i + 1} of {iterations}")
        imgcast.publish(image)
        time.sleep(10)
    imgcast.stop()


if __name__ == "__main__":
    _main()
