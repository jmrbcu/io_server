__author__ = 'jmrbcu'

# construct imports
from construct import Validator, Container, Struct, UBInt8


class CRC(Validator):

    def __init__(self, subcon):
        Validator.__init__(self, subcon)
        # self.valids = valids

    def _validate(self, obj, context):
        return  obj == self._crc(context)

    def _crc(self, context):
        crc = 0
        for k, v in context.iteritems():
            if k.startswith("_"):
               continue

            if isinstance(v, int):
                crc ^= v
            elif isinstance(v, basestring):
                for char in v:
                    crc ^= ord(char)
            elif isinstance(v, Container):
                crc ^= self._crc(v)

        return crc

crc = Struct('crc', CRC(UBInt8('crc')))