__author__ = 'jmrbcu'

# construtc imports
from construct import Struct, OneOf, Byte, String, Embed

# card reader imports
from crc import crc

# magnetic stripe command markers
MS_STX = 0x02 # start of command
MS_ETX = 0x03 # end of command

# operation modes
MS_MODES = (0x31, )

# response codes
MS_RESPONSE_STATUS = (0x06, 0x15)

# message structure
ms_cmd = Struct(
    'ms_msg',
    OneOf(Byte('start'), (MS_STX,)),
    OneOf(Byte('mode'), MS_MODES),
    Byte('track1_id'),
    Byte('track1_len'),
    OneOf(Byte('track1_status'), MS_RESPONSE_STATUS),
    String('track1', lambda ctx: ctx['track1_len']),
    Byte('track2_id'),
    Byte('track2_len'),
    OneOf(Byte('track2_status'), MS_RESPONSE_STATUS),
    String('track2', lambda ctx: ctx['track2_len']),
    Byte('track3_id'),
    Byte('track3_len'),
    OneOf(Byte('track3_status'), MS_RESPONSE_STATUS),
    String('track3', lambda ctx: ctx['track3_len']),
    OneOf(Byte('stop'), (MS_ETX,)),
    Embed(crc)
)
