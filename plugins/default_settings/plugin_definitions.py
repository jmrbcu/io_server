# -*- coding: utf-8 -*-
# foundation imports
from foundation.plugin_manager import Plugin


class DefaultSettingsPlugin(Plugin):
    id = 'plugins.default_settings'
    name = 'Default Settings Plugin'
    version = '0.1'
    description = 'Default Settings Plugin'
    platform = 'all'
    author = ['Jose M. Rodriguez Bacallao']
    author_email = 'jmrbcu@gmail.com'
    depends = []
    enabled = True

    def configure(self):
        from foundation.application import application
        settings = application.settings
        settings.setdefault('redis_server', 'localhost')


