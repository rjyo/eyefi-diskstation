#!/usr/bin/python

# EyeFi Python Server
#
# Copyright (C) 2010 Robert Jordens
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

import os

import eyefi.log as logger
import eyefi.config as config

log = logger.setup_custom_logger()

from eyefi.geotag import handle_photo


def main():
    path = config.data["upload_dir"]

    files = [os.path.join(root, name)
             for root, dirs, files in os.walk(path)
             for name in files
             if name.lower().endswith(".log")]

    while len(files):
        handle_photo(files)


if __name__ == '__main__':
    main()
