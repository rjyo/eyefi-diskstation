# coding=utf-8

"""
# EyeFi Python Server
#
# Copyright (C) 2013 Rakuraku Jyo
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

import json
import os
import urllib2

import eyefi.log as logger
import eyefi.config as config

log = logger.get_custom_logger()

_LOC_BASE_URL = 'https://www.googleapis.com/geolocation/v1/geolocate?key=%s'
_TEMPLATE = '''<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="XMP Core 4.4.0">
   <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
      <rdf:Description rdf:about=""
            xmlns:exif="http://ns.adobe.com/exif/1.0/">
         <exif:GPSLatitude>%s</exif:GPSLatitude>
         <exif:GPSLongitude>%s</exif:GPSLongitude>
         <exif:GPSMapDatum>WGS-84</exif:GPSMapDatum>
      </rdf:Description>
   </rdf:RDF>
</x:xmpmeta>
<?xpacket end="r"?>
'''


def mac_fmt(mac):
    return ":".join(mac[2 * i:2 * i + 2] for i in range(6))


def eyefi_parse(logfile):
    photos, aps = {}, {}
    for line in open(logfile):
        power_secs, secs, event = line.strip().split(",", 2)
        event = event.split(",")
        event, args = event[0], event[1:]
        if event == "POWERON":
            yield photos, aps
            photos, aps = {}, {}
        elif event in ("AP", "NEWAP"):
            mac, strength, data = args
            aps.setdefault(mac, []).append({
                "power_secs": int(power_secs),
                "secs": int(secs),
                "signal_to_noise": int(strength),
                "data": int(data, 16),
            })
        elif event == "NEWPHOTO":
            filename, size = args
            photos[filename] = {
                "power_secs": int(power_secs),
                "secs": int(secs),
                "size": int(size),
            }
        else:
            raise ValueError, "unknown event %s" % line
        yield photos, aps


def photo_macs(photo, aps):
    t = photo["power_secs"]
    macs = []
    for mac in aps:
        seen = min([(abs(m["power_secs"] - t), m["signal_to_noise"])
                    for m in aps[mac]], key=lambda a: a[0])
        if seen[0] <= 3600:
            macs.append({"macAddress": mac_fmt(mac),
                         "age": seen[0] * 1000,
                         "signalToNoiseRatio": seen[1]})
    return macs


def google_loc(macs):
    """
    Use google Geolocation API to locate the position with MAC addresses collected
    https://developers.google.com/maps/documentation/business/geolocation/

    :param macs: A list of MAC addresses
    :returns: Location with lat and lng from google as a diction
    :rtype: dict
    """

    # Google can't find geo location with just one mac address
    if len(macs) < 2:
        return ""

    data = json.dumps({"wifiAccessPoints": macs})

    log.debug("Sending data to google geo API: %s", data)

    req = urllib2.Request(_LOC_BASE_URL % config.data["google_geo_key"], data, {'Content-Type': 'application/json'})
    try:
        f = urllib2.urlopen(req)
        r = f.read()
        f.close()
        return json.loads(r)
    except urllib2.HTTPError, err:
        if err.code == 403:
            log.error("Google API rate limit exceeded")
        raise err


def write_gps(filename, lat, lng):
    f = open(filename, 'w')
    xmp = _TEMPLATE % (lat, lng)
    f.write(xmp)
    log.debug("%s saved" % filename)


def handle_photo(files):
    logName = [f for f in files if f.lower().endswith(".log")][0]
    data = list(eyefi_parse(logName))

    xmpName = logName[:-8] + '.xmp'
    dirName, name = os.path.split(logName)
    name = name[:-4]

    if not os.access(xmpName, os.R_OK):
        for photos, aps in data[::-1]:  # take newest first
            if name in photos:
                # log.debug(photos)
                macs = photo_macs(photos[name], aps)

                loc = google_loc(macs)
                if loc:
                    log.debug("geo tagged %s" % name)
                    loc = loc["location"]
                    write_gps(xmpName, loc["lat"], loc["lng"])

                    break
    else:
        log.debug("%s already existed, skipping" % xmpName)

    files.remove(logName)
    os.remove(logName)
