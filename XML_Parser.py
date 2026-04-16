import xml.etree.ElementTree as ET

##Intial set up requires uploading code from a local file
##It will be expected that in the future the XML file will be uploaded to a system ##

#Parse the XML file and get the root element
tree = ET.parse(##Insert XML file path here##)
root = tree.getroot()

