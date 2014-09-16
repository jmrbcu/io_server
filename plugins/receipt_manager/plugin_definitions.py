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
        from .receipt_manager import ReceiptManager

        settings = application.settings
        settings = settings['ReceiptManager']
        printer = settings['printer']

        return ReceiptManager(self.id, printer),

    def configure(self):
        receipts_path = path(application.home_dir).join('receipts')
        settings = application.settings
        settings = settings.setdefault('ReceiptManager', {})
        settings.setdefault('printer', 'default')



