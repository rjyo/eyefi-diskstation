#!/usr/bin/python

"""
# Copyright (c) 2009, Jeffrey Tchang
# Additional *pike
# Additional 2013 by Rakuraku Jyo
#
# All rights reserved.
#
#
# THIS SOFTWARE IS PROVIDED ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import cgi

import sys
import os
import socket
from datetime import datetime

import hashlib
import binascii
import tarfile

import xml.sax
import xml.dom.minidom

from BaseHTTPServer import BaseHTTPRequestHandler
import BaseHTTPServer
import SocketServer
import StringIO

from eyefi.sax_handler import EyeFiContentHandler
from eyefi.geotag import handle_photo
import eyefi.config as config
import eyefi.log as logger

log = logger.setup_custom_logger()

# General architecture notes
#
#
# This is a standalone Eye-Fi Server that is designed to take the place of the Eye-Fi Manager.
#
#
# Starting this server creates a listener on port 59278. I use the BaseHTTPServer class included
# with Python. I look for specific POST/GET request URLs and execute functions based on those
# URLs.

# Implements an EyeFi server


class EyeFiServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    def server_bind(self):

        BaseHTTPServer.HTTPServer.server_bind(self)
        self.socket.settimeout(None)
        self.run = True

    def get_request(self):
        while self.run:
            try:
                connection, address = self.socket.accept()
                log.debug("Incoming connection from client %s" % address[0])

                connection.settimeout(None)
                return connection, address

            except socket.timeout:
                pass


# This class is responsible for handling HTTP requests passed to it.
# It implements the two most common HTTP methods, do_GET() and do_POST()

class EyeFiRequestHandler(BaseHTTPRequestHandler):
    # Overriding options
    protocol_version = 'HTTP/1.1'
    sys_version = ""
    server_version = "Eye-Fi Agent/2.0.4.0 (Windows XP SP2)"

    def do_GET(self):
        log.debug(self.command + " " + self.path + " " + self.request_version)

        log.debug("Headers received in GET request:")
        for headerName in self.headers.keys():
            for headerValue in self.headers.getheaders(headerName):
                log.debug(headerName + ": " + headerValue)

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(self.client_address)
        self.wfile.write(self.headers)
        self.close_connection = 0

    def do_POST(self):
        log.debug(self.command + " " + self.path + " " + self.request_version)

        SOAPAction = ""
        contentLength = ""

        # Loop through all the request headers and pick out ones that are relevant

        log.debug("Headers received in POST request:")
        for headerName in self.headers.keys():
            for headerValue in self.headers.getheaders(headerName):

                if headerName == "soapaction":
                    SOAPAction = headerValue

                if "content-length" == headerName:
                    contentLength = int(headerValue)

                log.debug(headerName + ": " + headerValue)

        # Read contentLength bytes worth of data
        log.debug("Attempting to read " + str(contentLength) + " bytes of data")
        postData = self.rfile.read(contentLength)
        log.debug("Finished reading " + str(contentLength) + " bytes of data")

        # Perform action based on path and SOAPAction
        # A SOAPAction of StartSession indicates the beginning of an EyeFi
        # authentication request
        if (self.path == "/api/soap/eyefilm/v1") and (SOAPAction == "\"urn:StartSession\""):
            log.debug("Got StartSession request")
            self.do_response(self.startSession(postData))
            self.handle_one_request()

        # GetPhotoStatus allows the card to query if a photo has been uploaded
        # to the server yet
        if (self.path == "/api/soap/eyefilm/v1") and (SOAPAction == "\"urn:GetPhotoStatus\""):
            log.debug("Got GetPhotoStatus request")
            self.do_response(self.getPhotoStatus(postData))

        # If the URL is upload and there is no SOAPAction the card is ready to send a picture to me
        if (self.path == "/api/soap/eyefilm/v1/upload") and (SOAPAction == ""):
            log.debug("Got upload request")
            self.do_response(self.uploadPhoto(postData))

        # If the URL is upload and SOAPAction is MarkLastPhotoInRoll
        if (self.path == "/api/soap/eyefilm/v1") and (SOAPAction == "\"urn:MarkLastPhotoInRoll\""):
            log.debug("Got MarkLastPhotoInRoll request")
            self.do_response(self.markLastPhotoInRoll(postData), close=True)

    def do_response(self, response, close=False):
        log.debug("response: " + response)
        self.send_response(200)
        self.send_header('Date', self.date_time_string())
        self.send_header('Pragma', 'no-cache')
        self.send_header('Server', 'Eye-Fi Agent/2.0.4.0 (Windows XP SP2)')
        self.send_header('Content-Type', 'text/xml; charset="utf-8"')
        self.send_header('Content-Length', len(response))
        if close:
            self.send_header('Connection', 'Close')
            log.debug("Connection closed.")
        self.end_headers()
        self.wfile.write(response)
        self.wfile.flush()

    def render_xml(self, name, elements):
        # Create the XML document to send back
        doc = xml.dom.minidom.Document()

        element = doc.createElement(name)
        element.setAttribute("xmlns", "http://localhost/api/soap/eyefilm")

        for k in elements:
            e = doc.createElement(k)
            e.appendChild(doc.createTextNode(elements[k]))
            element.appendChild(e)

        SOAPElement = doc.createElementNS("http://schemas.xmlsoap.org/soap/envelope/", "SOAP-ENV:Envelope")
        SOAPElement.setAttribute("xmlns:SOAP-ENV", "http://schemas.xmlsoap.org/soap/envelope/")
        SOAPBodyElement = doc.createElement("SOAP-ENV:Body")
        SOAPBodyElement.appendChild(element)
        SOAPElement.appendChild(SOAPBodyElement)
        doc.appendChild(SOAPElement)

        return doc.toxml(encoding="UTF-8")

    def send_eyefi_header(self, length, close=False):
        self.send_response(200)
        self.send_header('Date', self.date_time_string())
        self.send_header('Pragma', 'no-cache')
        self.send_header('Server', 'Eye-Fi Agent/2.0.4.0 (Windows XP SP2)')
        self.send_header('Content-Type', 'text/xml; charset="utf-8"')
        self.send_header('Content-Length', length)
        if close:
            self.send_header('Connection', 'Close')
        self.end_headers()

    # Handles MarkLastPhotoInRoll action
    def markLastPhotoInRoll(self, postData):
        return self.render_xml("MarkLastPhotoInRollResponse", {})

    # Handles receiving the actual photograph from the card.
    # postData will most likely contain multipart binary post data that needs to be parsed
    def uploadPhoto(self, postData):
        # Take the postData string and work with it as if it were a file object
        postDataInMemoryFile = StringIO.StringIO(postData)

        # Get the content-type header which looks something like this
        # content-type: multipart/form-data; boundary=---------------------------02468ace13579bdfcafebabef00d
        contentTypeHeader = self.headers.getheaders('content-type').pop()
        log.debug(contentTypeHeader)

        # Extract the boundary parameter in the content-type header
        headerParameters = contentTypeHeader.split(";")
        log.debug(headerParameters)

        boundary = headerParameters[1].split("=")
        boundary = boundary[1].strip()
        log.debug("Extracted boundary: " + boundary)

        # eyeFiLogger.debug("uploadPhoto postData: " + postData)

        # Parse the multipart/form-data
        form = cgi.parse_multipart(postDataInMemoryFile, {"boundary": boundary,
                                                          "content-disposition": self.headers.getheaders(
                                                              'content-disposition')})
        log.debug("Available multipart/form-data: " + str(form.keys()))

        # Parse the SOAPENVELOPE using the EyeFiContentHandler()
        soapEnvelope = form['SOAPENVELOPE'][0]
        log.debug("SOAPENVELOPE: " + soapEnvelope)
        handler = EyeFiContentHandler()
        xml.sax.parseString(soapEnvelope, handler)

        log.debug("Extracted elements: " + str(handler.extractedElements))

        imageTarfileName = handler.extractedElements["filename"]

        now = datetime.now()
        uploadDir = now.strftime(config.data["upload_dir"] + config.data["upload_subdir"])
        if not os.path.isdir(uploadDir):
            os.makedirs(uploadDir)

        imageTarPath = os.path.join(uploadDir, imageTarfileName)
        log.debug("Generated path " + imageTarPath)

        log.debug("Opened file " + imageTarPath + " for binary writing")
        fileHandle = open(imageTarPath, 'wb')
        fileHandle.write(form['FILENAME'][0])
        fileHandle.close()

        log.debug("Extracting TAR file " + imageTarPath)
        imageTarfile = tarfile.open(imageTarPath)
        imageTarfile.extractall(path=uploadDir)
        imageTarfile.close()

        log.debug("Deleting TAR file " + imageTarPath)
        os.remove(imageTarPath)

        # process log
        process_logs()

        return self.render_xml("UploadPhotoResponse", {"success": "true"})

    def getPhotoStatus(self, postData):
        handler = EyeFiContentHandler()
        xml.sax.parseString(postData, handler)

        return self.render_xml("GetPhotoStatusResponse", {"field": "1", "offset": "0"})

    def startSession(self, postData):
        log.debug("Delegating the XML parsing of startSession postData to EyeFiContentHandler()")
        handler = EyeFiContentHandler()
        xml.sax.parseString(postData, handler)

        log.debug("Extracted elements: " + str(handler.extractedElements))
        log.debug("Setting Eye-Fi upload key to " + config.data["upload_key"])

        credentialString = handler.extractedElements["macaddress"] + handler.extractedElements[
            "cnonce"] + config.data["upload_key"]
        log.debug("Concatenated credential string (pre MD5): " + credentialString)

        # Return the binary data represented by the hexadecimal string
        # resulting in something that looks like "\x00\x18V\x03\x04..."
        binaryCredentialString = binascii.unhexlify(credentialString)

        # Now MD5 hash the binary string
        m = hashlib.md5()
        m.update(binaryCredentialString)

        # Hex encode the hash to obtain the final credential string
        credential = m.hexdigest()

        return self.render_xml("StartSessionResponse", {
            "credential": credential,
            "snonce": "99208c155fc1883579cf0812ec0fe6d2",
            "transfermode": "2",
            "transfermodetimestamp": "1230268824",
            "upsyncallowed": "false"
        })


def process_logs():
    path = config.data["upload_dir"]
    log.debug("Start to process files under %s", path)

    files = [os.path.join(root, name)
             for root, dirs, files in os.walk(path)
             for name in files
             if name.lower().endswith(".log")]

    while len(files):
        handle_photo(files)


def start_server():
    server_address = config.data["host_name"], config.data["host_port"]

    try:
        # Create an instance of an HTTP server. Requests will be handled by EyeFiRequestHandler
        server = EyeFiServer(server_address, EyeFiRequestHandler)
        server.config = config

        log.info("Eye-Fi server started listening on port " + str(server_address[1]))
        server.serve_forever()
    except KeyboardInterrupt:
        server.socket.close()
        server.shutdown()
        log.info("Eye-Fi server stopped")


def main():
    if len(sys.argv) == 1:
        print "usage: %s [ start | process ]" % os.path.basename(sys.argv[0])
        print "  start   - start the eye-fi server"
        print "  process - process the log files for geo locations"
        sys.exit(2)

    # open file logging
    logger.setup_logfile(config.data["log_file"])

    if sys.argv[1] == 'start':
        start_server()
    elif sys.argv[1] == 'process':
        if not config.data["google_geo_key"]:
            print("Google Geolocation API key not found. Using undocumented google geo API")
        process_logs()


if __name__ == '__main__':
    main()
