# -*- coding: utf-8 -*-
__author__ = 'jmrbcu'

# python imports
import logging
import json
import time
import datetime

# redis imports
import redis

# io_server imports
from core.utils import subscribe, lr_justify
from core.escpos.printer import Usb

# application runner plugin imports
from application_runner.plugin_application import PluginApplication

logger = logging.getLogger(__file__)


class ReceiptManagerApp(PluginApplication):
    """
    Plugin application from managing receipts. It manage the action of
    sending receipts to several destinations, for instance, printer,
    sms and email, but, we just support sending receipts to the attached
    Thermal pinter. We uses a local redis server as communication channel.

    Redis Communication Channels:
        receipts.commands: Command channel
        receipt.responses: Response channel

    Command Message Format:
        The commands should be in json format and must conform
        to the following standard:

        format: {
            "command": "command type",
            "params": {
                "param0": value,
                ...
                "paramN": values
            }
        }

        Commands:
            send_receipt:
                Send a receipt to a destination. The destination
                could be the printer, an email address or a text
                to a given phone number.

            Parameters:
                destination: A list where the first element is the destination
                type and could be one of these: "printer", "sms", "email".
                The remaining parameters are optional and they depends on the
                destination type. So far, this is what we support:
                    "destination": ["printer"]
                    "destination": ["sms", "10 digits phone number"]
                    "destination": ["email", "email address"]

                driver_name: The driver name, E.g. "driver_name": "Jon Smith"

                cab_id: The ID of the cab, E.g. "cab_id": "AHX0102"

                items: The items purchased during the trip. It is a dictionary
                where the keys are the purchased item names and the values are
                lists where the first element is the price tag and the second
                one the item type. Items types can be: "item", "barcode" and
                "qrcode". The barcode or qrcode generated will be based on the
                item name.

                promotions: The promotions given to the client during the trip.
                It is a dictionary where the keys are the promotion names and
                the values are the promotion type and can be: "barcode",
                "qrcode". The barcode or qrcode generated will be based on the
                promotion name.

            E.g.: {
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

    Responses/Events Message Format:
        The response for a given command or an event type.
        The responses/events commands are in json format conform
        to the following standard:

        format: {
            "command": "command type",
            "params": {
                "param0": value,
                ...
                "paramN": values
            }
        }


        Responses/Events:
            send_receipt:
                Response to the command "send_receipt", it describe if the
                command was executed successfully or not.

            Parameters:
                error: True if an error happened, False otherwise.
                E.g.: "error": false

                error_code: The error code if an error happened, 0 otherwise.
                E.g.: "error_code": 0

                status: Status string representing some informative message
                about the response. Will contain the error string in case
                of error.
                E.g.: status: "Printer not connected"

            E.g.: {
                "command": "send_receipt",
                "params": {
                    "error": false,
                    "error_code": 0,
                    "status": ""
                }
            }

            E.g.: {
                "command": "send_receipt",
                "params": {
                    "error": true,
                    "error_code": 1,
                    "status": "printer not connected"
                }
            }
    """

    # communication channels
    COMMAND_CHANNEL = 'receipt_manager.commands'
    RESPONSE_CHANNEL = 'receipt_manager.responses'

    # error codes
    (OK, FORMAT_ERROR, INVALID_COMMAND, PRINTER_ERROR, UNKNOWN_ERROR) = range(5)

    def __init__(self, appid, id_vendor, id_product, interface=0,
                 in_ep=0x82, out_ep=0x01, header=None, footer=None):
        super(ReceiptManagerApp, self).__init__(appid)
        self.id_vendor = id_vendor
        self.id_product = id_product
        self.interface = interface
        self.in_ep = in_ep
        self.out_ep = out_ep
        self.header = header.strip()
        self.footer = footer.strip()

    def run(self):
        try:
            # message handler
            handler = subscribe(
                ReceiptManagerApp.COMMAND_CHANNEL, self.on_message
            )

            # main loop
            while True:
                time.sleep(0.1)
        except (SystemExit, KeyboardInterrupt):
            handler.stop()

    def on_message(self, msg):
        logger.info('New command received: {0}'.format(msg))

        try:
            command = msg['command']
            params = msg['params']

            if command == 'send_receipt':
                destination = params['destination']
                driver_name = params['driver_name']
                cab_id = params['cab_id']
                items = params['items']
                promotions = params['promotions']

                if destination[0] == 'printer':
                    success = self.print_receipt(
                        driver_name, cab_id, items, promotions
                    )
                    if success:
                        success, error_code, status = (
                            True, ReceiptManagerApp.OK, 'OK'
                        )
                    else:
                        msg = 'Failed to print receipt'
                        success, error_code, status = (
                            False, ReceiptManagerApp.PRINTER_ERROR, msg
                        )
                else:
                    success, error_code, status = (
                        False, ReceiptManagerApp.INVALID_COMMAND,
                        ('Invalid destination: {0}, for now, we only support'
                         'printer as destination').format(destination)
                    )
            else:
                success, error_code, status = (
                    False, ReceiptManagerApp.INVALID_COMMAND,
                    'Invalid command: {0}'.format(command)
                )
        except (KeyError, IndexError) as e:
            success, error_code, status = (
                False, ReceiptManagerApp.FORMAT_ERROR,
                'Message format error, could not find key: {0}'.format(e)
            )
        except Exception as e:
            success, error_code, status = (
                False, ReceiptManagerApp.UNKNOWN_ERROR, str(e)
            )

        if success:
            logger.info(status)
        else:
            logger.error(status)

        self.send_response(success, error_code, status)

    def print_receipt(self, driver_name, cab_id, items, promotions):
        printer = Usb(
            int(self.id_vendor, 16), int(self.id_product, 16),
            int(self.interface, 16), int(self.in_ep, 16),
            int(self.out_ep, 16)
        )

        try:
            # print header if we have one
            if self.header:
                printer.set(align='center')
                printer.image(self.header)
                printer.line(initial_break=False)

            # print date and time
            now = datetime.datetime.now()
            date = datetime.datetime.strftime(now, '%m/%d/%Y')
            time = datetime.datetime.strftime(now, '%I:%M %p')

            printer.set(align='left')
            printer.text('DATE: {0} {1}\n'.format(date, time))

            # print driver name and cab id
            printer.set(align='left')
            printer.text('DRIVER NAME: {0}\n'.format(driver_name))
            printer.text('CAB ID: {0}\n'.format(cab_id))
            printer.line()

            # print items
            extras = {}
            subtotal = 0.0
            for name, (price, itype) in items.iteritems():
                price = float(price)
                left = '{0}:'.format(name)
                right = '{0:.2f}'.format(price)
                to_print = lr_justify(left, right, 32)
                if itype in ('barcode', 'qrcode'):
                    printer.set(align='left', type='u2')
                    printer.text(to_print)
                    extras[name] = itype
                else:
                    printer.set(align='left', type='normal')
                    printer.text(to_print)
                printer.text('\n')
                subtotal += price
            tax = 0.0825 * subtotal

            # print subtotals, taxes and totals
            printer.text('\n')
            printer.set(align='left', type='b')
            printer.text('SUBTOTAL:\t{0:.2f}\n'.format(subtotal))
            printer.text('TAXES:\t{0:.2f}\n'.format(tax))

            total = subtotal + tax
            printer.line(initial_break=False)
            printer.set(align='left', type='b')
            printer.text('TOTAL:\t{0:.2f}\n'.format(total))

            # print promotions and extras
            if promotions:
                printer.text('\n')
                printer.set(align='left', type='bu2')
                printer.text('PROMOTIONS:\n\n')

                printer.set(align='left', type='bu')
                for name, ptype in promotions.iteritems():
                    if ptype == 'barcode':
                        printer.text('{0}\n'.format(name))
                        printer.barcode(name,'UPC-A', 128, 2, 'OFF', 'B')
                    elif ptype == 'qrcode':
                        printer.text('{0}\n'.format(name))
                        printer.qr(name, True, qr_escpos_size=4)
                    else:
                        msg = 'Invalid promotion type: {0}'
                        logger.error(msg.format(ptype))
                printer.line()

            if extras:
                printer.text('\n')
                printer.set(align='left', type='bu2')
                printer.text('EXTRAS\n\n')

                printer.set(align='left', type='bu')
                for name, etype in extras.iteritems():
                    if etype == 'barcode':
                        printer.text('{0}\n'.format(name))
                        printer.barcode(name,'UPC-A', 128, 2, 'OFF', 'B')
                    elif etype == 'qrcode':
                        printer.text('{0}\n'.format(name))
                        printer.qr(name, True, qr_escpos_size=4)
                    else:
                        msg = 'Invalid extra type: {0}'
                        logger.error(msg.format(etype))
                printer.line()

            # print footer if we have one
            if self.footer:
                printer.line(initial_break=True)
                printer.set(align='center')
                printer.image(self.footer)

            printer.cut()
            return True
        except Exception as e:
            logger.error(e)
            return False
        finally:
            printer.close()

    def send_response(self,  success, error_code, status):
        try:
            msg = json.dumps({
                "command": "send_receipt",
                "params": {
                    "error": not success,
                    "error_code": error_code,
                    "status": status,
                }
            })
            pub = redis.StrictRedis()
            pub.publish(ReceiptManagerApp.RESPONSE_CHANNEL, msg)
        except Exception as e:
            logger.error(e)
