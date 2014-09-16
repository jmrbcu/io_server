# -*- coding: utf-8 -*-
# foundation imports
from foundation.plugin_manager import Plugin, contributes_to


class DeviceChargerPlugin(Plugin):
    id = 'plugins.applications.device_charger'
    name = 'Device Charger Application Plugin'
    version = '0.1'
    description = 'Device Charger Application Plugin'
    platform = 'all'
    author = ['Jose M. Rodriguez Bacallao']
    author_email = 'jmrbcu@gmail.com'
    depends = ['plugins.app_runner']
    enabled = True

    @contributes_to('application_runner.applications')
    def _create(self):
        from .device_charger import DeviceCharger
        return DeviceCharger(self.id),
