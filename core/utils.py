__author__ = 'jmrbcu'

# python imports
import threading
import Queue
import redis
import time
import logging
import json

logger = logging.getLogger(__file__)


def lr_justify(left, right, width):
    """
    Justify an string at the left and the right using
    maximum "width" characters
    """
    if len(left) + len(right) > width - 1:
        left = left[:width - len(right) - 1]

    return '{}{}{}'.format(left, ' '*(width-len(left+right)), right)


def subscribe(channel, handler, host='localhost', port=6379,
              db=0, password=None):

    class WorkerThread(threading.Thread):
        def __init__(self, *args, **kwargs):
            super(WorkerThread, self).__init__(*args, **kwargs)
            self.args = args
            self.kwargs = kwargs
            self.daemon = True
            self._stop = False

        def run(self):
            client = redis.StrictRedis(host, port, db, password)
            pubsub = client.pubsub(ignore_subscribe_messages=True)

            logger.info('Starting to wait for commands in: {0}'.format(channel))
            while not self._stop:
                try:
                    if not pubsub.subscribed:
                        pubsub.subscribe(channel)

                    msg = pubsub.get_message(ignore_subscribe_messages=True)
                    if msg is not None:
                        handler(json.loads(msg['data']), *self.args, **self.kwargs)
                    else:
                        time.sleep(0.01)
                except redis.ConnectionError:
                    error = 'Error while connecting to redis, reconnecting...'
                    logger.error(error)
                    time.sleep(1)
                except Exception as e:
                    logger.error(e)

        def stop(self):
            self._stop = True
            self.join()

    worker = WorkerThread()
    worker.start()
    return worker

if __name__ == '__main__':
    def test_handler(results, msg):
        worker = threading.current_thread()
        print 'From: ', worker, 'sending message: ', msg
        results.put(msg)

    # results = Queue()
    handler = subscribe('test', test_handler)
    while True:
        try:
            msg = handler.results.get(timeout=0.1)
            print 'From: ', threading.current_thread(), ' receiving message: ', msg
        except Queue.Empty:
            pass
        except (KeyboardInterrupt, SystemExit):
            handler.stop()
            break
    print 'Exited'