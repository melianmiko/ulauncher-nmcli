import os
import subprocess

import dbus
from dbus.mainloop.glib import DBusGMainLoop

DBusGMainLoop(set_as_default=True)
system = dbus.SystemBus()


def send_notification(text):
    subprocess.run(["notify-send",
                    "-h", "int:transient:1",
                    "--icon=" + os.path.dirname(os.path.realpath(__file__)) + "/images/icon.png",
                    text,
                    "ULauncher NetworkManager"
                    ])


def get_active_connection_uuids():
    manager = system.get_object("org.freedesktop.NetworkManager",
                                "/org/freedesktop/NetworkManager")
    manager = dbus.Interface(manager, "org.freedesktop.DBus.Properties")
    active_paths = manager.Get("org.freedesktop.NetworkManager", "ActiveConnections")
    active_connections = []

    for path in active_paths:
        active_con = system.get_object("org.freedesktop.NetworkManager", path)
        active_con = dbus.Interface(active_con, "org.freedesktop.DBus.Properties")
        con_path = active_con.Get("org.freedesktop.NetworkManager.Connection.Active", "Connection")

        con_data = system.get_object("org.freedesktop.NetworkManager", con_path)
        con_data = dbus.Interface(con_data, "org.freedesktop.NetworkManager.Settings.Connection").GetSettings()

        uuid = str(con_data["connection"]["uuid"])
        active_connections.append(uuid)

    return active_connections


def connect(uuid):
    log = subprocess.run(["nmcli", "connection", "up", uuid], stdout=subprocess.PIPE)
    active_cons = get_active_connection_uuids()
    result = uuid in active_cons
    return str(log.stdout, "utf-8"), result


def disconnect(uuid):
    log = subprocess.run(["nmcli", "connection", "down", uuid], stdout=subprocess.PIPE)
    active_cons = get_active_connection_uuids()
    result = uuid not in active_cons
    return str(log.stdout, "utf-8"), result


def get_connections():
    active_connections = get_active_connection_uuids()

    settings = system.get_object("org.freedesktop.NetworkManager",
                                 "/org/freedesktop/NetworkManager/Settings")
    settings = dbus.Interface(settings, "org.freedesktop.NetworkManager.Settings")
    paths = settings.ListConnections()

    connections = []
    for path in paths:
        con_data = system.get_object("org.freedesktop.NetworkManager", path)
        con_data = dbus.Interface(con_data, "org.freedesktop.NetworkManager.Settings.Connection").GetSettings()

        connections.append({
            "name": str(con_data["connection"]["id"]),
            "uuid": str(con_data["connection"]["uuid"]),
            "type": str(con_data["connection"]["type"]),
            "active": str(con_data["connection"]["uuid"]) in active_connections
        })

    return connections
