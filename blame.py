#!/usr/bin/env python3

from lxml import html
import json

config = json.loads(open("config.json").read())

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
                self.logger.error("HTML not loaded before requestign lines")
            return

        xpath_author = config['BLAME']['XPATH_BLAME_AUTHOR']

        matches = self.html_tree.xpath(xpath_author, line = str(line))
        
        if len(matches) == 1:
            return matches[0].text
        else:
            if self.logger != None:
                self.logger.error("Error while finding author for line {} no matches found", str(line))
            return ""