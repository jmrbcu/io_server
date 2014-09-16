# -*- coding: utf-8 -*-
__author__ = 'jmrbcu'

# python imports
import logging
import signal


logger = logging.getLogger(__file__)

signals = (
    signal.SIGILL, signal.SIGQUIT, signal.SIGTRAP, signal.SIGABRT,
    signal.SIGFPE, signal.SIGBUS, signal.SIGSEGV, signal.SIGSYS,
    signal.SIGPIPE, signal.SIGTERM, signal.SIGTSTP, signal.SIGTTIN,
    signal.SIGTTOU, signal.SIGXCPU, signal.SIGXFSZ, signal.SIGVTALRM,
    signal.SIGPROF, signal.SIGALRM, signal.SIGUSR2, signal.SIGINT
)

class PluginApplication(object):

    def __init__(self, appid):
        self.appid = appid
        self._stop = False

    def run(self):
        pass

    def stop(self):
        logger.info('Stop plugin application: {0} requested'.format(self.appid))
        self._stop = True
