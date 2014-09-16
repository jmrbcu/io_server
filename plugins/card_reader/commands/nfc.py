__author__ = 'jmrbcu'

# construct imports
from construct import Struct, OneOf, Byte, UBInt16, Embed, String, Container

# card reader imports
from crc import crc

# NFC start and end markers
NFC_STX = 0x02 # start of transmision
NFC_ETX = 0x03 # end of transmision

# NFC device classes
NFC_COMMAND_CLASS_IN = 0x01 # internal execution command
NFC_COMMAND_CLASS_RF = 0x02 # RF card command
NFC_COMMAND_CLASS_IC = 0x03 # IC card command
NFC_COMMAND_CLASS_MS = 0x04 # Magnetic Stripes card command

# NFC commands
NFC_GET_VERSION = 0xA0
MS_DIRECT_COMMAND = 0xC1
NFC_COMMAND_SET = (MS_DIRECT_COMMAND, NFC_GET_VERSION)

# NFC COMMAND RESPONSE SET
SUCCESS = 0x00
COMMAND_ERROR = 0x01
PACKET_ERROR = 0x02
STATUS_ERROR = 0x03
PROCESS_ERROR = 0x04
BCC_ERROR = 0x05
CARD_NO_EXIST = 0x06
LENGTH_ERROR = 0x07
PARAMETER_ERROR = 0x08
TIMEOUT_ERROR = 0x09
FIRMWARE_BCC_ERROR = 0x0A

NFC_RESPONSE_SET = (
    SUCCESS, COMMAND_ERROR, PACKET_ERROR, STATUS_ERROR,
    PROCESS_ERROR, BCC_ERROR, CARD_NO_EXIST, LENGTH_ERROR,
    PARAMETER_ERROR, TIMEOUT_ERROR, FIRMWARE_BCC_ERROR
)


def nfc_cmd(cmd):
    return Struct('nfc_msg',
        OneOf(Byte('start'), (NFC_STX,)),
        OneOf(Byte('device'), NFC_RESPONSE_SET),
        OneOf(Byte('command'), NFC_COMMAND_SET),
        UBInt16('len'),
        String('data', lambda ctx: ctx['len']) if cmd is None else cmd,
        OneOf(Byte('stop'), (NFC_ETX, )),
        Embed(crc)
    )
