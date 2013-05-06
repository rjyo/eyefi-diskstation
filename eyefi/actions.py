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

from twisted.python import log

# geotag
from eyefi.maclog import eyefi_parse, photo_macs
from eyefi.google_loc import google_loc
from eyefi.exif_gps import write_gps

class Action(object):
    name = "action_name"

    def __init__(self, cfg, card):
        pass

    @classmethod
    def active_on_card(cls, card):
        return bool(card.get(cls.name, False))

    def handle_photo(self, card, files):
        pass

    def __call__(self, args):
        return self.handle_photo(*args)



class Geotag(Action):
    name = "geotag"

    def handle_photo(self, card, files):
        logname = [f for f in files if f.lower().endswith(".log")][0]
        photoname = [f for f in files if f is not log][0]
        dir, name = os.path.split(photoname)
        data = list(eyefi_parse(logname))
        for photos, aps in data[::-1]: # take newest first
            if name in photos:
                macs = photo_macs(photos[name], aps)
                loc = google_loc(wifi_towers=macs)
                loc.addCallback(self._write_loc, photoname,
                        sidecar=card["geotag_sidecar"],
                        xmp=card["geotag_xmp"])
                loc.addCallback(log.msg, "geotagged")
                if card["geotag_delete_log"]:
                    loc.addCallback(lambda _: os.remove(logname))
                    files.remove(logname)
                loc.addCallback(lambda _: (card, files))
                return loc
        return card, files # no log

    @staticmethod
    def _write_loc(loc, photo, sidecar=True, xmp=False):
        if sidecar or photo.lower().endswith(".jpg"):
            loc = loc["location"]
            write_gps(photo,
                loc["latitude"], loc["longitude"], loc.get("altitude", None),
                "WGS-84", loc.get("accuracy", None), sidecar, xmp)
        return loc, photo
