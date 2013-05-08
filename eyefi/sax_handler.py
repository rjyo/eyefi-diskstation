"""
# Copyright (c) 2009, Jeffrey Tchang
# Extracted to separated module by Rakuraku Jyo
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

from xml.sax.handler import ContentHandler


# Eye Fi XML SAX ContentHandler
class EyeFiContentHandler(ContentHandler):
    # These are the element names that I want to parse out of the XML
    elementNamesToExtract = ["macaddress", "cnonce", "transfermode", "transfermodetimestamp", "fileid", "filename",
                             "filesize", "filesignature"]

    # For each of the element names I create a dictionary with the value to False
    elementsToExtract = {}

    # Where to put the extracted values
    extractedElements = {}

    def __init__(self):
        ContentHandler.__init__(self)
        self.extractedElements = {}
        for elementName in self.elementNamesToExtract:
            self.elementsToExtract[elementName] = False

    def startElement(self, name, attributes):
        # If the name of the element is a key in the dictionary elementsToExtract
        # set the value to True
        if name in self.elementsToExtract:
            self.elementsToExtract[name] = True

    def endElement(self, name):
        # If the name of the element is a key in the dictionary elementsToExtract
        # set the value to False
        if name in self.elementsToExtract:
            self.elementsToExtract[name] = False

    def characters(self, content):
        for elementName in self.elementsToExtract:
            if self.elementsToExtract[elementName]:
                self.extractedElements[elementName] = content
