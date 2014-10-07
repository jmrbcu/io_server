__author__ = 'jmrbcu'

import sys
import redis
import json
import time
import threading

COMMAND_CHANNEL = 'receipt_manager.commands'
RESPONSE_CHANNEL = 'receipt_manager.responses'


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


def send_receipt():
    pub = redis.StrictRedis()
    command = {
        "command": "send_receipt",
        "params": {
            "destination": ["printer"],
            "driver_name": "Jon Smith",
            "cab_id": "AH0001234",
            "items": {
                "Top up to phone: 713-345-6745": [10.0, 'item'],
                "T-Shirt on amazon": [3.00, "barcode"],
                "Phone charge": [2.00, "item"],
                "Trip Fare": [15.00, "item"]
            },
            "promotions": {
                "Space Center Free Ticket": "qrcode"
            }
        }
    }
    pub.publish(COMMAND_CHANNEL, json.dumps(command))


if __name__ == '__main__':
    try:
        listener = Listener()
        listener.start()

        while True:
            command = raw_input().upper()
            if command == 'P':
                send_receipt()
            else:
                msg = 'Error: valid commands are (R)ead'
                print msg
    except (KeyboardInterrupt, SystemExit):
        pass