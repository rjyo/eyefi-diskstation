#!/usr/bin/python

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



