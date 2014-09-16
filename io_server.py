# -*- coding: utf-8 -*-
__author__ = 'jmrbcu'

# foundation imports
from foundation.paths import path

# totaltrack imports
from foundation.application import Application


def start():
    application = Application('io_server', '1.0')
    application.start()

if __name__ == '__main__':
    start()
