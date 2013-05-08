"""
# Copyright (c) 2013, Rakuraku Jyo
# All rights reserved.
#
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import logging

# shared logging format
logFormat = logging.Formatter("[%(asctime)s][%(funcName)s] - %(message)s", '%m/%d/%y %I:%M%p')


def get_custom_logger():
    return logging.getLogger("eyeFiLogger")


def setup_custom_logger():
    # Create the main logger
    logger = get_custom_logger()
    logger.setLevel(logging.DEBUG)

    # Create two handlers. One to print to the log and one to print to the console
    consoleHandler = logging.StreamHandler()
    # Set how both handlers will print the pretty log events
    consoleHandler.setFormatter(logFormat)
    # Append both handlers to the main Eye Fi Server logger
    logger.addHandler(consoleHandler)

    return logger


def setup_logfile(logfile):
    logger = get_custom_logger()
    fileHandler = logging.FileHandler(logfile, "w", encoding=None)
    fileHandler.setFormatter(logFormat)
    logger.addHandler(fileHandler)
