#!/usr/bin/env python3

from lxml import html
import json, sys, logging
import requests

config = json.loads(open("config.json").read())

module = sys.modules['__main__'].__file__
log = logging.getLogger(module)

class BlameParser:

    def __init__(self, project_link, logger = None):
        self.project_link = project_link
        self.logger = logger
        self.html_tree = None

    def load_blame_page(self, commit, file):
        blame_url = self.project_link + "/blame/" + commit + file
        page = requests.get(blame_url)

        self.html_tree = html.fromstring(page.content)

    def load_sample_blame_page(self):
        with open(config['BLAME']['TEST_FILE']) as file:
            self.html_tree = html.fromstring(file.read())

    def get_author_from_blame(self, line):
        if self.html_tree == None:
            if self.logger != None:
                self.logger.error("HTML not loaded before requesting lines")
            return

        xpath_author = config['BLAME']['XPATH_BLAME_AUTHOR']

        matches = self.html_tree.xpath(xpath_author, line = str(line))
        
        if len(matches) == 1:
            return matches[0].text
        else:
            if self.logger != None:
                self.logger.error("No author found for line {}".format(line))
            return ""

if __name__ == "__main__":
    logging.basicConfig(stream=sys.stderr, format='%(name)s %(levelname)s %(message)s')
    blamer = BlameParser(project_link='', logger=log)
    blamer.load_sample_blame_page()
    author = blamer.get_author_from_blame(28)
    print(author)
