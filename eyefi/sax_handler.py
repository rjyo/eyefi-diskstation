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
