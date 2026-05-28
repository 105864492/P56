# src/parser.py
import xml.sax
import xml.sax.handler
from src.config import DBLP_XML, PUBLICATION_TYPES, MAX_RECORDS


class DBLPHandler(xml.sax.handler.ContentHandler):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.current_type = None
        self.current_record = {}
        self.current_field = None
        self.current_chars = []
        self.count = 0
        self.done = False

    def startElement(self, name, attrs):
        if self.done:
            return

        if name in PUBLICATION_TYPES:
            self.current_type = name
            self.current_record = {
                "type": name,
                "key": attrs.get("key", None),
                "authors": [],
            }

        elif self.current_type:
            self.current_field = name
            self.current_chars = []

    def characters(self, content):
        if self.current_field:
            self.current_chars.append(content)

    def endElement(self, name):
        if self.done:
            return

        if name in PUBLICATION_TYPES and self.current_type == name:
            self.callback(self.current_record)
            self.count += 1
            self.current_type = None
            self.current_record = {}
            self.current_field = None

            if MAX_RECORDS and self.count >= MAX_RECORDS:
                self.done = True

        elif self.current_type and self.current_field == name:
            value = "".join(self.current_chars).strip()

            if name == "author":
                self.current_record["authors"].append(value)
            elif name in ("journal", "booktitle"):
                self.current_record["venue"] = value
            else:
                self.current_record[name] = value

            self.current_field = None
            self.current_chars = []


def parse_dblp(callback):
    handler = DBLPHandler(callback)

    with open(DBLP_XML, "rb") as f:
        try:
            xml.sax.parse(f, handler)
        except StopIteration:
            pass

    print(f"Parsed {handler.count:,} records")
    return handler.count