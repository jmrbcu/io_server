__author__ = 'jmrbcu'

import redis
import json
import time
import threading

COMMAND_CHANNEL = 'card_reader.commands'
RESPONSE_CHANNEL = 'card_reader.responses'


class Listener(threading.Thread):

    def __init__(self, *args, **kwargs):
        super(Listener, self).__init__(*args, **kwargs)
        self.daemon = True
        self._stop = False

    def run(self):
        client = redis.StrictRedis()
        pubsub = client.pubsub(ignore_subscribe_messages=True)
        pubsub.subscribe(RESPONSE_CHANNEL)

        while not self._stop:
            try:
                if not pubsub.subscribed:
                    pubsub.subscribe(RESPONSE_CHANNEL)

                msg = pubsub.get_message(ignore_subscribe_messages=True)
                if msg is not None:
                    print msg['data']
                else:
                    time.sleep(0.01)
            except redis.ConnectionError:
                error = 'Error while connecting to redis, reconnecting...'
                print error
                time.sleep(1)
            except Exception as e:
                print e

    def stop(self):
        self._stop = True
        self.join()


def read():
    pub = redis.StrictRedis()
    command = {
        "command": "read",
        "params": {
            "timeout": 5
        }
    }
    pub.publish(COMMAND_CHANNEL, json.dumps(command))


if __name__ == '__main__':
    try:
        listener = Listener()
        listener.start()

        while True:
            command = raw_input().upper()
            if command == 'R':
                read()
            else:
                msg = 'Error: valid commands are (R)ead'
                print msg
    except (KeyboardInterrupt, SystemExit):
        pass