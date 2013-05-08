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


data = dict()
# host name and port to listen on
# you can leave hostname empty for localhost

data["host_name"] = ""
data["host_port"] = 59278

# To use this script you need to have your Eye-Fi upload key.
# You can find it after configuring the card, 
# which you can currently on do on windows or mac
# It is inside C = \Documents and Settings\<User>\Application Data\Eye-Fi\Settings.xml on windows
# or ~/Applications Data/Eye-Fi/Settings.xml on mac
# search for it and paste it here = 

data["upload_key"] = "29abc93a62e9cb84d07e6d3f1c892a2f"

# When connecting, all files are downloaded in one directory
# the name of the directory can be a strftime formatted string like 
# /home/myblog/pictures/%%Y-%%m-%%d
# notice the double percent sign to escape % from ini interpolation

data["upload_dir"] = "/tmp/eyefifolder"
data["upload_subdir"] = "/%Y/%Y-%m-%d"

# Get you own geolocation API key from:
# https://developers.google.com/maps/documentation/business/geolocation/

data["google_geo_key"] = ""

data["log_file"] = "/tmp/eyefi.log"