# python imports
import logging

# foundation imports
from foundation.application import application as core_app

logger = logging.getLogger(__name__)


class ApplicationRunner(object):
    def __init__(self, applications):
        self.applications = applications

    def start(self):
        app = None
        options = core_app.options
        appid = options.application

        logger.info('Looking for application: {0}'.format(appid))
        for application in self.applications:
            if application.appid == appid:
                app = application

        if app is None:
            logger.info('No application found')
            return

        logger.info('Starting application: {0}'.format(app.appid))
        app.run()
        logger.info('Stopping application: {0}'.format(app.appid))
