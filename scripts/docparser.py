from bs4 import BeautifulSoup
import sys
import os
import json


def get_section(doc, section):
    element = doc.find(section)
    if element:
        return element.get_text()


def get_description(doc):
    text = get_section(doc, "refsect1")
    if text:
        lines = filter(lambda x: x.strip(), text.split("\n"))

        if len(lines) > 1 and lines[0] == "Description":
            return lines[0] + "\n" + lines[1]


def parse(file_name):
    with open(file_name, "r") as file:
        doc = BeautifulSoup(file.read(), "html.parser")
        return {
            "description": get_description(doc),
            "synopsis": get_section(doc, "synopsis")
        }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Parse postgres SGML reference files into JSON")
        print("Usage:")
        print("echo -n \"commands = \" > command_help.py; python parser.py ref/ | python -mjson.tool | sed 's/\"\: null/\": None/g' >>  command_help.py")
        print("")
        sys.exit(0)

    dir = sys.argv[1]
    docs = {}

    for file_name in os.listdir(dir):
        if file_name.endswith(".sgml"):
            path = dir.rstrip("/") + "/" + file_name
            command = file_name[:-5].replace("_", " ")
            docs[command.upper()] = parse(path)
    print(json.dumps(docs))
