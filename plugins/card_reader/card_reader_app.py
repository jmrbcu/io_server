# -*- coding: utf-8 -*-
__author__ = 'jmrbcu'

# python imports
import re
import json
import time
import logging

# redis imports
import redis

# io_server imports
from core.utils import subscribe

# application runner plugin imports
from application_runner.plugin_application import PluginApplication

# card reader imports
from .reader import MSReader, Timeout

logger = logging.getLogger(__file__)


class CardReaderApp(PluginApplication):
    """
    Plugin application from reading information from card readers.
    It uses a local redis server as communication channel.
    Initially, it only supports Magnetic Stripe Readers.

    Redis Communication Channels:
        card_reader.commands: Command channel
        card_reader.responses: Response channel

    Commands:
        The commands should be in json format and must conform
        to the following standard:

        read: Read the information contained in a card
        format: {
            "command": "read",
            "params": {
                "timeout": 30
            }
        }

    Responses/Events:
        The responses commands are in json format conform
        to the following standard:

        card_info: Notify when the card has been read or
        an error happened while reading it. Take into
        account that if a track is empty, it will not be
        included in the content field.

        format: {
            "command": "card_info",
            "params": {
                "error": true or false,
                "error_code": 0,
                "status": "status string"
                "content": {
                    "track1": "content of track 1",
                    "track2": "content of track 2",
                    "track3": "content of track 3"
                }
            }
        }
    """

    # communication channels
    COMMAND_CHANNEL = 'card_reader.commands'
    RESPONSE_CHANNEL = 'card_reader.responses'

    # error codes
    (OK, EMPTY_TRACKS, TIMEOUT, FORMAT_ERROR, INVALID_COMMAND, UNKNOWN_ERROR) = range(6)

    def __init__(self, appid):
        super(CardReaderApp, self).__init__(appid)

        # reader
        self.reader = None

        # monitor stop flag
        self._stop = False

    def run(self):
        # message handler
        handler = subscribe(CardReaderApp.COMMAND_CHANNEL, self.on_message)

        # detect where the magnetic reader is connected
        device = MSReader.detect_reader()
        if device is None:
            return
        self.reader = MSReader(device)

        # main loop
        try:
            while True:
                time.sleep(0.1)
        except (SystemExit, KeyboardInterrupt):
            handler.stop()
            self.reader.close()

    def on_message(self, msg):
        logger.info('New command received: {0}'.format(msg))
        tracks = None

        try:
            command = msg['command']
            params = msg['params']

            if command == 'read':
                timeout = params['timeout']
                tracks = self.reader.read(timeout)
                if tracks:
                    success, error_code, status, tracks = (
                        True, CardReaderApp.OK, 'OK', tracks
                    )
                else:
                    success, error_code, status = (
                        False, CardReaderApp.EMPTY_TRACKS, 'empty tracks'
                    )
            else:
                success, error_code, status = (
                    False, CardReaderApp.INVALID_COMMAND,
                    'Invalid command: {0}'.format(command)
                )
        except Timeout:
            success, error_code, status = (
                False, CardReaderApp.TIMEOUT, 'Reading process has timed out'
            )
        except KeyError as e:
            success, error_code, status = (
                False, CardReaderApp.FORMAT_ERROR,
                'Message format error, could not find key: {0}'.format(e)
            )
        except Exception as e:
            success, error_code, status = (
                False, CardReaderApp.UNKNOWN_ERROR, str(e)
            )

        if success:
            logger.info(status)
        else:
            logger.error(status)
        self.send_response(success, error_code, status, tracks)

    def send_response(self,  success, error_code, status, tracks=None):
        try:
            pub = redis.StrictRedis()
            msg = self._build_message(success, error_code, status, tracks)
            pub.publish(CardReaderApp.RESPONSE_CHANNEL, msg)
        except Exception as e:
            logger.error(e)

    def _build_message(self, success, error_code, status, tracks=None):
        content = {
            'track{0}'.format(k): v for k, v in enumerate(tracks)
        } if tracks else {}

        return json.dumps({
            "command": "card_info",
            "params": {
                "error": not success,
                "error_code": error_code,
                "status": status,
                "content": content
            }
        })