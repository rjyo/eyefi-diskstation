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



import simplejson
from twisted.web.client import getPage

LOC_BASE_URL = 'http://www.google.com/loc/json'


def google_loc(*macs, **args):
    """
    https://developers.google.com/maps/documentation/business/geolocation/
    """
    base = {
        "version": "1.1.0",
        "host": "maps.google.com",
        }
    base.update(args)
    for mac in macs:
        base.setdefault("wifi_towers", []).append({"mac_address": mac})
    d = getPage(LOC_BASE_URL, method="POST",
            postdata=simplejson.dumps(base))
    d.addCallback(simplejson.loads)
    return d

def main():
    from twisted.internet import reactor
    from twisted.python import log
    import sys
    log.startLogging(sys.stdout)
    google_loc(sys.argv[1:], request_address=True).addBoth(
            log.msg).addBoth(lambda e: reactor.callLater(0, reactor.stop))
    reactor.run()

if __name__ == '__main__':
    main()
