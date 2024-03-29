# -*- coding: utf-8 -*-
"""
Presence analyzer web app.
"""

import logging.config
import os.path

import presence_analyzer.views

from presence_analyzer.main import app

if __name__ == "__main__":
    ini_filename = os.path.join(os.path.dirname(__file__),
                                '..', 'runtime', 'debug.ini')
    logging.config.fileConfig(ini_filename, disable_existing_loggers=False)
    app.run(host='0.0.0.0')
