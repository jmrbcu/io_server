# -*- coding: utf-8 -*-
__author__ = 'jmrbcu'

# python imports
import logging
import json
import datetime

# gevent imports
import gevent
from gevent.monkey import patch_all
from gevent.subprocess import check_call, check_output
patch_all(thread=False)

# redis imports
import redis

# reportlab imports
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

# pycups imports
import cups

# jinja imports
from jinja2 import Template

# foundation imports
from foundation.paths import path
from foundation.application import application

# application runner plugin imports
from application_runner.plugin_application import PluginApplication

logger = logging.getLogger(__file__)


class RedisClientError(Exception):
    pass


class MessageFormatError(Exception):
    pass


class ReceiptCreationError(Exception):
    pass


class PrintError(Exception):
    pass


class ReceiptManager(PluginApplication):

    def __init__(self, appid, printer):
        super(ReceiptManager, self).__init__(appid)
        self.printer = printer
        self.host = application.settings.get('redis_server', 'localhost')

        # redis connectors
        self._publisher = redis.Redis(self.host)
        self._receiver = redis.Redis(self.host)
        self._subscriber = self._receiver.pubsub(ignore_subscribe_messages=True)

        # receipt management
        self.receipt = 'receipt.pdf'
        self.spool = path(application.home_dir).join('spool')
        if not self.spool.exists():
            self.spool.makedirs()

        self.template = None
        self.template_path = path(__file__).dirname().join('res').join('default_template.html')
        with open(self.template_path) as f:
            self.template = f.read()

    def run(self):
        while True:
            try:
                logger.info('Starting to wait for receipt orders')
                if not self._subscriber.subscribed:
                    self._subscriber.subscribe('receipts.orders')

                for msg in self._subscriber.listen():
                    self.process_order(msg)
            except redis.ConnectionError:
                error = 'Error while connecting to redis, reconnecting...'
                logger.error(error)
                gevent.sleep(1)
            except (KeyboardInterrupt, SystemExit):
                break
            except:
                error = 'Unhandled exception within loop'
                logger.error(error, exc_info=True)

    def process_order(self, msg):
        try:
            logger.info('New message received: {0}'.format(msg))

            data = msg.get('data')
            if data is None:
                raise MessageFormatError('Empty message, discarding')
            data = json.loads(data)

            # validate the message
            self._validate_message(data)

            # get all required params
            destination = data.get('destination', 'printer')
            driver_name = data.get('driver_name', 'Default Driver')
            cab_number = data.get('cab_number', 'XXXXXXXXXXXX')
            items = data.get('items')

            # create pdf receipt
            receipt = self.create_receipt(self.receipt, driver_name, cab_number, items)

            # print the receipt
            self.print_receipt(receipt)

            # send the response if everything was OK
            self.send_response(True, 'OK')
        except (MessageFormatError, ReceiptCreationError, PrintError) as e:
            logger.error(e)
            self.send_response(False, e.message)
        finally:
            self._cleanup()

    def create_receipt(self, receipt, name, plate, items):
        now = datetime.datetime.now()
        date = datetime.datetime.strftime(now, '%m/%d/%Y')
        time = datetime.datetime.strftime(now, '%I:%M %p')

        subtotal = 0.0
        item_names, prices = [], []
        for item, price in items:
            price = float(price)
            subtotal += price
            item_names.append(item)
            prices.append('{0:.2f}'.format(price))
        tax = 0.0825 * subtotal
        total = subtotal + tax

        template = Template(self.template)
        output = template.render(
            name=name, plate=plate, date=date, time=time,
            items=item_names, prices=prices,
            subtotal=subtotal, tax=tax, total=total
        )

        html = self.spool.join('output.html')
        pdf = self.spool.join('output.pdf')
        path(__file__).dirname().join('res').join('header.jpeg').copy(self.spool)
        path(__file__).dirname().join('res').join('footer.jpeg').copy(self.spool)
        with open(html, 'w') as f:
            f.write(output)

        check_call(['wkhtmltopdf', '--page-width', '48', '--page-height', '140', '-T', '0', '-B', '0', '-L', '0', '-R', '0', html, pdf])
        return pdf


    def create_receipt_old(self, receipt, driver_name, cab_number, items):
        width, height = 48 * mm, 140 * mm
        margin = 10

        pdf = canvas.Canvas(receipt, pagesize=(width, height))
        pdf.setLineWidth(.3)
        pdf.setFont('Helvetica', 7)

        # start writing the receipt
        title = 'YELLOW CAB'
        pdf.drawCentredString(width/2, height - 14, title)
        pdf.line(margin, height - 16, width - margin, height - 16)

        text = pdf.beginText(margin, height - 30)
        text.textLine('Driver Name: ' + driver_name)
        text.textLine('Cab Number: ' + cab_number)
        text.textLine('Date: ' + datetime.datetime.now().ctime())
        text.textLine('')

        total = 0.0
        for item, price in items:
            text.textLine(item + ': ' + '$' + str(price))
            total += price
        pdf.drawText(text)

        x0, y0 = text.getStartOfLine()
        pdf.line(x0, y0 -1, width - margin, y0)
        pdf.drawRightString(width - margin, y0 - 10, 'Total: ' + '$' + '{0:0.2f}'.format(total))
        pdf.drawString(margin, y0 - 24, 'Thank You')
        pdf.drawString(margin, y0 - 32, 'www.houstonyellowcab.com')

        # save the pdf file
        pdf.save()

    def print_receipt(self, receipt):
        connection = cups.Connection()
        if self.printer == 'default':
            printer = connection.getDefault()
        connection.cancelAllJobs(printer)
        connection.disablePrinter(printer)
        connection.enablePrinter(printer)
        connection.acceptJobs(printer)

        pid = connection.printFile(printer, receipt, 'receipt', {})
        if pid == 0:
            raise PrintError('An error has occurred while printing')

        timeout = 30
        while connection.getJobs().get(pid, None) is not None and timeout:
            logger.info(connection.getJobs())
            gevent.sleep(1)
            timeout -= 1

        if timeout == 0:
            connection.cancelAllJobs(printer)
            raise PrintError('Printer job has timed out')

    def send_response(self, result, reason):
        logger.info('Sending response to subscribers: {0}'.format(result))
        msg = {'result': result, 'reason': reason}
        self._publisher.publish('receipts.results', json.dumps(msg))

    def _cleanup(self):
        try:
            for filename in self.spool.listdir():
                logger.info('Cleaning file: {0}'.format(filename))
                filename.remove()
        except:
            pass

    def _validate_message(self, data):
        destination = data.get('destination')
        if destination is None:
            error = 'Missing destination field in message, discarding'
            raise MessageFormatError(error)

        driver_name = data.get('driver_name')
        if driver_name is None:
            error = 'Missing driver name field in message, discarding'
            raise MessageFormatError(error)

        cab_number = data.get('cab_number')
        if cab_number is None:
            error = 'Missing cab number field in message, discarding'
            raise MessageFormatError(error)

        items = data.get('items')
        if items is None:
            error = 'Missing items field in message, discarding'
            raise MessageFormatError(error)

        if not isinstance(items, list) or isinstance(items, tuple):
            error = 'Bad format for items field, discarding message: {0}'
            raise MessageFormatError(error.format(items))

