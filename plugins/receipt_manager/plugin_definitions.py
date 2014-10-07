# -*- coding: utf-8 -*-
# foundation imports
from foundation.paths import path
from foundation.application import application
from foundation.plugin_manager import Plugin, contributes_to


class ReceiptManagerPlugin(Plugin):
    id = 'plugins.applications.receipt_manager'
    name = 'Receipt Manager Application Plugin'
    version = '0.1'
    description = 'Receipt Manager Application Plugin'
    platform = 'all'
    author = ['Jose M. Rodriguez Bacallao']
    author_email = 'jmrbcu@gmail.com'
    depends = ['plugins.app_runner']
    enabled = True

    @contributes_to('application_runner.applications')
    def _create(self):
        from .receipt_manager_app import ReceiptManagerApp

        settings = application.settings
        settings = settings['ReceiptManager']

        printer = settings['printer']
        id_vendor = printer['id_vendor']
        id_product = printer['id_product']
        interface = printer['interface']
        in_ep = printer['in_ep']
        out_ep = printer['out_ep']
        header = printer['header']
        footer = printer['footer']

        return ReceiptManagerApp(self.id, id_vendor, id_product, interface,
                                 in_ep, out_ep, header, footer),

    def configure(self):
        default_header = path(__file__).dirname().join('res').join('logo.jpg')
        default_footer = default_header

        settings = application.settings
        settings = settings.setdefault('ReceiptManager', {})
        printer = settings.setdefault('printer', {})
        printer.setdefault('id_vendor', '')
        printer.setdefault('id_product', '')
        printer.setdefault('interface', 0)
        printer.setdefault('in_ep', 0x82)
        printer.setdefault('out_ep', 0x01)
        printer.setdefault('header', default_header)
        printer.setdefault('footer', default_footer)




