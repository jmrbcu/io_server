# -*- coding: utf-8 -*-
__author__ = 'jmrbcu'

# python imports
import re
import json
import time
import threading
import logging

# pyserial imports
from serial import Serial
from serial.tools import list_ports

# redis imports
import redis

# foundation imports
from foundation.paths import path
from foundation.application import application

# io_server imports
from core.utils import subscribe

# application runner plugin imports
from application_runner.plugin_application import PluginApplication

logger = logging.getLogger(__file__)


class DeviceCharger(PluginApplication):
    """
    Plugin application that manages device charging. It uses a local redis
    server as communication channel. Its main function is to take care of the
    charging commands sent through a redis channel and let listeners on
    the response channel know when something happens, for instance, a device
    was plugged/unplugged, error conditions, etc.
    This class interface with the "USB Switchable Charger" device connected
    using the serial or usb ports.

    Redis Communication Channels:
        device_charger.commands: Command channel
        device_charger.responses: Response channel

    Commands:
        The commands should be in json format and must conform
        to the following standard:

        enable_charging: Enable charging for the connected device
        format: {"command": "enable_charging"}

        disable_charging: Disable charging for the connected device
        format: {"command": "disable_charging"}

        device_status: Get the device status using the response channel
        format: {"command": "device_status"}

    Responses/Events:
        The responses commands are in json format conform
        to the following standard:

        device_connected: Notify that a device was connected and is not charging
        format: {"command": "device_connected"}

        device_disconnected: Notify that a device was disconnected
        format: {"command": "device_disconnected"}

        device_status: Get the connected device status
        format: {
            "command": "device_status",
            "params": {
                "status": "status string"
            }
        }
    """

    # communication channels
    COMMAND_CHANNEL = 'device_charger.commands'
    RESPONSE_CHANNEL = 'device_charger.responses'

    # commands
    ENABLE_CHARGING = 'E'
    DISABLE_CHARGING = 'D'
    STATUS = 'S'
    IDENTIFICATION = 'I'

    def __init__(self, appid):
        super(DeviceCharger, self).__init__(appid)
        # USB Switchable Charger interface
        self.charger = None

        # monitor stop flag
        self._stop = False

    @staticmethod
    def detect_charger_port():
        ports = [port[0] for port in list_ports.grep('2341:8037')]
        if ports:
            return ports[0]

        ports = [port[0] for port in list_ports.grep('0403:6001')]
        return ports[0] if ports else None

    def enable_charging(self, enable):
        if self.charger is None:
            return

        if enable:
            self.charger.write(DeviceCharger.ENABLE_CHARGING)
        else:
            self.charger.write(DeviceCharger.DISABLE_CHARGING)

    def send_status(self):
        if self.charger is None:
            return
        self.charger.write(DeviceCharger.STATUS)

    def run(self):
        # detect USB Switchable charger port
        port = DeviceCharger.detect_charger_port()
        if port is None:
            msg = 'None of the ports contains a USB Switchable charger, exiting'
            logger.error(msg)
            return

        # connect to the charger device using its serial interface
        try:
            self.charger = Serial(port, 9600, 8, 'N', 1, timeout=0.5)
        except (OSError, IOError) as e:
            logger.error(e)
            return

        # start charger status watcher
        charger_watcher = self.start_watcher(self.charger)

        # command handler
        command_handler = subscribe(DeviceCharger.COMMAND_CHANNEL,
                                    self.on_command)
        try:
            while True:
                time.sleep(0.1)
        except (SystemExit, KeyboardInterrupt):
            command_handler.stop()
            charger_watcher.stop()
            self.enable_charging(False)

    def on_command(self, command):
        try:
            logger.info('New command received: {0}'.format(command))
            command = command.get('command')
        except Exception as e:
            msg = 'Message format not valid: {0}'.format(command)
            logger.error(msg)

        try:
            if command == 'enable_charging':
                self.enable_charging(True)
            elif command == 'disable_charging':
                self.enable_charging(False)
            elif command == 'device_status':
                self.send_status()
        except Exception as e:
            logger.error(e)

    def start_watcher(self, charger):

        class ChargerWatcher(threading.Thread):
            def __init__(self, *args, **kwargs):
                super(ChargerWatcher, self).__init__(*args, **kwargs)
                self.daemon = True
                self._stop = False

            def run(self):
                status_re = '\w+:\w+'
                publisher = redis.StrictRedis()

                while not self._stop:
                    line = charger.readline().strip()
                    if not line:
                        continue

                    logger.info('New charger event: {0}'.format(line))
                    msg = None
                    if line == 'connected':
                        msg = {'command': 'device_connected'}
                    elif line == 'disconnected':
                        msg = {'command': 'device_disconnected'}
                    elif re.match(status_re, line):
                        msg = {
                            'command': 'device_status',
                            'params': {
                                'status': line
                            }
                        }
                    else:
                        logger.error('Unknown command: {0}'.format(line))
                        continue

                    publisher.publish(DeviceCharger.RESPONSE_CHANNEL,
                                      json.dumps(msg))

            def stop(self):
                self._stop = True
                self.join()

        charger_watcher = ChargerWatcher()
        charger_watcher.start()
        return charger_watcher
