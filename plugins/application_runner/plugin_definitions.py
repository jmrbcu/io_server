# -*- coding: utf-8 -*-
# iat imports
from foundation.plugin_manager import Plugin, ExtensionPoint, contributes_to


class ApplicationRunnerPlugin(Plugin):
    id = 'plugins.app_runner'
    name = 'Application Runner Plugin'
    version = '0.1'
    description = 'Application Runner plugin'
    platform = 'all'
    author = ['Jose M. Rodriguez Bacallao']
    author_email = 'jmrbcu@gmail.com'
    depends = ['plugins.default_settings']
    enabled = True

    applications = ExtensionPoint('application_runner.applications')

    def enable(self):
        from .application_runner import ApplicationRunner
        runner = ApplicationRunner(self.applications)
        self.plugin_manager.register_service('core.application', runner)

    @contributes_to('application.arguments')
    def add_arguments(self):
        from foundation.application import Argument

        return (
            Argument(
                '-a', '--application',
                help='Id of the desired plugin application to run'
            ),
        )


