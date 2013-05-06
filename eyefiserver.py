#!/usr/bin/env python

"""
* Copyright (c) 2009, Jeffrey Tchang
* Additional *pike
* All rights reserved.
*
*
* THIS SOFTWARE IS PROVIDED ''AS IS'' AND ANY
* EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
* WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
* DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY
* DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
* (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
* LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
* ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
* (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
* SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import cgi

import sys
import os
import socket
import StringIO
import ConfigParser
from datetime import datetime

import hashlib
import binascii
import tarfile

import xml.sax
import xml.dom.minidom

from BaseHTTPServer import BaseHTTPRequestHandler
import BaseHTTPServer
import SocketServer

from eyefi.sax_handler import EyeFiContentHandler
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

                #def stop(self):
                #  self.run = False

                # alt serve_forever method for python <2.6
                # because we want a shutdown mech ..
                #def serve(self):
                #  while self.run:
                #    self.handle_request()
                #  self.socket.close()


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
            response = self.startSession(postData)
            contentLength = len(response)

            log.debug("StartSession response: " + response)

            self.send_eyefi_header(contentLength)

            self.wfile.write(response)
            self.wfile.flush()
            self.handle_one_request()

        # GetPhotoStatus allows the card to query if a photo has been uploaded
        # to the server yet
        if (self.path == "/api/soap/eyefilm/v1") and (SOAPAction == "\"urn:GetPhotoStatus\""):
            log.debug("Got GetPhotoStatus request")

            response = self.getPhotoStatus(postData)
            contentLength = len(response)

            log.debug("GetPhotoStatus response: " + response)

            self.send_eyefi_header(contentLength)

            self.wfile.write(response)
            self.wfile.flush()

        # If the URL is upload and there is no SOAPAction the card is ready to send a picture to me
        if (self.path == "/api/soap/eyefilm/v1/upload") and (SOAPAction == ""):
            log.debug("Got upload request")
            response = self.uploadPhoto(postData)
            contentLength = len(response)

            log.debug("Upload response: " + response)

            self.send_eyefi_header(contentLength)

            self.wfile.write(response)
            self.wfile.flush()

        # If the URL is upload and SOAPAction is MarkLastPhotoInRoll
        if (self.path == "/api/soap/eyefilm/v1") and (SOAPAction == "\"urn:MarkLastPhotoInRoll\""):
            log.debug("Got MarkLastPhotoInRoll request")
            response = self.markLastPhotoInRoll(postData)
            contentLength = len(response)

            log.debug("MarkLastPhotoInRoll response: " + response)
            self.send_eyefi_header(contentLength, close=True)

            self.wfile.write(response)
            self.wfile.flush()

            log.debug("Connection closed.")

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
        # Create the XML document to send back
        doc = xml.dom.minidom.Document()
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

        #pike
        #uid = self.server.config.getint('EyeFiServer','upload_uid')
        #gid = self.server.config.getint('EyeFiServer','upload_gid')
        #mode = self.server.config.get('EyeFiServer','upload_mode')
        #eyeFiLogger.debug("Using uid/gid %d/%d"%(uid,gid))
        #eyeFiLogger.debug("Using mode " + mode)

        now = datetime.now()
        uploadDir = now.strftime(self.server.config.get('EyeFiServer', 'upload_dir'))
        if not os.path.isdir(uploadDir):
            os.makedirs(uploadDir)
            #if uid!=0 and gid!=0:
            #  os.chown(uploadDir,uid,gid)
            #if mode!="":
            #  os.chmod(uploadDir,string.atoi(mode))

        imageTarPath = os.path.join(uploadDir, imageTarfileName)
        log.debug("Generated path " + imageTarPath)

        fileHandle = open(imageTarPath, 'wb')
        log.debug("Opened file " + imageTarPath + " for binary writing")

        fileHandle.write(form['FILENAME'][0])
        log.debug("Wrote file " + imageTarPath)

        fileHandle.close()
        log.debug("Closed file " + imageTarPath)

        #if uid!=0 and gid!=0:
        #  os.chown(imageTarPath,uid,gid)
        #if mode!="":
        #  os.chmod(imageTarPath,string.atoi(mode))

        log.debug("Extracting TAR file " + imageTarPath)
        imageTarfile = tarfile.open(imageTarPath)
        imageTarfile.extractall(path=uploadDir)

        log.debug("Closing TAR file " + imageTarPath)
        imageTarfile.close()

        log.debug("Deleting TAR file " + imageTarPath)
        os.remove(imageTarPath)

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

        # Retrieve it from C:\Documents and Settings\<User>\Application Data\Eye-Fi\Settings.xml

        log.debug("Setting Eye-Fi upload key to " + self.server.config.get('EyeFiServer', 'upload_key'))

        credentialString = handler.extractedElements["macaddress"] + handler.extractedElements[
            "cnonce"] + self.server.config.get('EyeFiServer', 'upload_key')
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


def main():
    if len(sys.argv) < 2:
        print "usage: %s configfile logfile" % os.path.basename(sys.argv[0])
        sys.exit(2)

    configfile = sys.argv[1]
    log.info("Reading config " + configfile)

    config = ConfigParser.SafeConfigParser()
    config.read(configfile)

    # open file logging
    logfile = sys.argv[2]
    logger.setup_logfile(logfile)

    server_address = (config.get('EyeFiServer', 'host_name'), config.getint('EyeFiServer', 'host_port'))

    try:
        # Create an instance of an HTTP server. Requests will be handled
        # by the class EyeFiRequestHandler
        eyeFiServer = EyeFiServer(server_address, EyeFiRequestHandler)
        eyeFiServer.config = config

        # Spawn a new thread for the server
        # thread.start_new_thread(eyeFiServer.serve, ())
        # eyeFiLogger.info("Eye-Fi server started listening on port " + str(server_address[1]))

        log.info("Eye-Fi server started listening on port " + str(server_address[1]))
        eyeFiServer.serve_forever()

        #raw_input("\nPress <RETURN> to stop server\n")
        #eyeFiServer.stop()
        #eyeFiLogger.info("Eye-Fi server stopped")
        #eyeFiServer.socket.close()

    except KeyboardInterrupt:
        eyeFiServer.socket.close()
        #eyeFiServer.shutdown()

        #eyeFiLogger.info("Eye-Fi server stopped")


if __name__ == '__main__':
    main()
