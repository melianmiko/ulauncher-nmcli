import logging
import os.path
import subprocess

import gi

import nm_tools

gi.require_version('Gdk', '3.0')

from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem

logger = logging.getLogger(__name__)

description_active = "{} | ACTIVE | Select to disconnect"
description_inactive = "{} | Select to connect"

class NetworkManagerExtension(Extension):
    def __init__(self):
        super(NetworkManagerExtension, self).__init__()

        # Subscribe plugin listeners to launcher
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())


class KeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        hidden_types = extension.preferences.get("hidden_type_list").split(",")
        connections = nm_tools.get_connections()
        connections = sorted(connections, key=lambda d: d["name"].lower())

        logger.debug(hidden_types)

        items = []
        for a in connections:
            description = description_active if a["active"] else description_inactive
            description = description.format(a["type"])
            icon_name = "{}_{}".format(a["type"], a["active"])
            icon_path = 'images/{}.png'.format(icon_name)

            if not os.path.isfile(icon_path):
                logger.warning("Icon not found: " + icon_path)

            if a["type"] in hidden_types:
                continue

            on_click_event = ExtensionCustomAction(a, keep_app_open=False)
            item_row = ExtensionResultItem(icon=icon_path,
                                           name=a["name"],
                                           description=description,
                                           on_enter=on_click_event)
            items.append(item_row)

        return RenderResultListAction(items)


class ItemEnterEventListener(EventListener):
    def on_event(self, event, extension):
        con = event.get_data()
        uuid = con["uuid"]

        if con["active"]:
            log, result = nm_tools.disconnect(uuid)
        else:
            log, result = nm_tools.connect(uuid)

        logging.debug(log)

        if not result:
            # Operation failed
            nm_tools.send_notification("Operation failed: " + log)
        elif con["active"]:
            # Success, disconnected
            nm_tools.send_notification("Now disconnected: " + con["name"])
        else:
            # Success, connected
            nm_tools.send_notification("Now connected: " + con["name"])

        script = extension.preferences.get("script_on_connect")
        if not con["active"] and script != "":
            subprocess.run([script, con["name"], con["uuid"]], stdout=subprocess.PIPE)


if __name__ == '__main__':
    NetworkManagerExtension().run()
