Eye-Fi Server for DiskStation
===

Eye-Fi server for DiskStation. Geotagging with xmp file supported.

If you are a DiskStation user, it would be great if your camera will upload all its photo to your DiskStation when the camera is the same local WiFi network.

This is a pure python implementation of Eye-Fi server. DiskStation has a linux with very limited libraries built in. It's also hard to compile most things on it. With  pure python implementation, it works on my DS413 with a powerpc CPU.

CONFIG
---
Config file is at `./eyefi/config.py`

To use this script you need to have your Eye-Fi upload key. You can find it after configuring the card, which you can currently on do on windows or mac. `C:\Documents and Settings\<User>\Application Data\Eye-Fi\Settings.xml on windows` or `~/Applications Data/Eye-Fi/Settings.xml` on mac

    data["upload_key"] = "YOUR_KEY"

All files are downloaded in one directory

    data["upload_dir"] = "/tmp/eyefifolder"
    data["upload_subdir"] = "/%Y/%Y-%m-%d"

Get you own geolocation API key from [Google](https://developers.google.com/maps/documentation/business/geolocation/). **If no key is given, an undocumented Google API will be used instead.**

    data["google_geo_key"] = ""

This is where your log file is saved

    data["log_file"] = "/tmp/eyefi.log"

RUN
---
To start and test, use

    git clone https://github.com/rjyo/eyefi-diskstation.git
    nohup /root/eyefi-diskstation/server.py start > /dev/null 2>&1 &

To start when disk-station reboots, edit `/etc/rc.local` and add the following lines

    # Eyefi-Server start
    [ -x /root/eyefi-diskstation/server.py ] && /root/eyefi-diskstation/server.py start

LICENSE
---
Sources from are the following open source projects are referenced and partly copied to this project

    https://github.com/tachang/EyeFiServer
    https://launchpad.net/eyefi‎
    https://github.com/omelhus/EyefiServerSynology
    
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

