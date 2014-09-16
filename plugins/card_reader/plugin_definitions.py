# -*- coding: utf-8 -*-
# foundation imports
from foundation.plugin_manager import Plugin, contributes_to


class CardReaderPlugin(Plugin):
    id = 'plugins.applications.card_reader'
    name = 'Card Reader Application Plugin'
    version = '0.1'
    description = 'Card Reader Application Plugin'
    platform = 'all'
    author = ['Jose M. Rodriguez Bacallao']
    author_email = 'jmrbcu@gmail.com'
    depends = ['plugins.app_runner']
    enabled = True

    @contributes_to('application_runner.applications')
    def _create(self):
        from .card_reader_app import CardReaderApp
        return CardReaderApp(self.id),
