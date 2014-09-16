__author__ = 'jmrbcu'

# python imports
import logging
import threading

# pyserial imports
from serial.tools import list_ports
from serial import Serial

# card reader plugin imports
from .commands.nfc import nfc_cmd
from .commands.ms import ms_cmd

logger = logging.getLogger(__file__)


class Timeout(Exception):
    pass


class SerialReader(object):

    def __init__(self, device=None):
        self.device = device
        self._stop = False
        self._timer = None
        self._timeout_event = threading.Event()

    @staticmethod
    def detect_reader():
        command = nfc_cmd(None)
        ports = list_ports.comports()

        for port, _, _ in ports:
            try:
                logger.info('Trying device in: {0}'.format(port))
                with Serial(port, 115200, 8, 'N', 1, timeout=0.1) as serial:
                    serial.write('\x02\x01\xA0\x00\x00\x03\xA0')
                    buff = serial.read(1000)
                    if not buff:
                        continue

                    container = command.parse(buff)
                    if 'NFC-1901' in container.data:
                        msg = 'Magnetic stripe reader found in: {0}'
                        logger.info(msg.format(port))
                        return port
            except Exception:
                continue

        logger.info('Magnetic stripe reader not found')
        return None

    def read(self, timeout=20):
        if self.device is None:
            return

        buff = ''
        self._stop = False

        # start the timer
        self._timer = threading.Timer(timeout, self._timeout_event.set)
        self._timer.start()

        with Serial(self.device, baudrate=115200, bytesize=8, stopbits=1,
                    parity='N', timeout=0.1) as serial:
            while not self._stop and not self._timeout_event.is_set():
                buff += serial.read(1024)
                if buff and serial.inWaiting() == 0:
                    break

        if self._timeout_event.is_set():
            self.close()
            raise Timeout('Card reading has timed out')

        self.close()
        return buff

    def close(self):
        self._timeout_event.clear()
        if self._timer is not None and self._timer.is_alive():
            self._timer.cancel()
        self._stop = True


class MSReader(SerialReader):

    def read(self, timeout=20, raw=False):
        result = super(MSReader, self).read(timeout)
        if raw:
            return result

        msg = nfc_cmd(ms_cmd).parse(result).ms_msg
        tracks = (
            (msg.track1, msg.track1_status),
            (msg.track2, msg.track2_status),
            (msg.track3, msg.track3_status)
        )

        return [track for track, status in tracks if status == 0x6]
