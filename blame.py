#!/usr/bin/env python3

import json, sys, logging
from collections import OrderedDict
import requests
from lxml import html
from models import LineBlame

module = sys.modules['__main__'].__file__
log = logging.getLogger(module)

class BlameParser:

    def __init__(self, project_link, logger = None):
        self.project_link = project_link
        self.logger = logger or logging
        self.blame_data = OrderedDict()

    def _parse_gh_blame_html(self, string):
        html_tree = html.fromstring(string)
        expression = ".//table[contains(@class, 'blame-container')]"
        container = html_tree.xpath(expression).pop()
        blame = None
        for e in container.iterchildren():
            # Every <tr class="blame-commit">commit info</tr> element
            # is followed by the corresponding lines in
            # <tr class="blame-line">line info</tr> elements
            if e.get('class') == 'blame-commit':
                blame = LineBlame(*[None]*6)
                sha_anchor = e.find('.//a[@class="blame-sha"]')
                blame.short_sha = sha_anchor.text
                blame.commit_url = sha_anchor.get('href')
                blame.avatar_url = e.xpath(".//img[contains(@class, 'avatar')]").pop().get('src')
                blame.commit_message = e.find('.//a[@class="message"]').get('title')
                blame.user_name = e.find('.//a[@rel="contributor"]').text
                blame.time = e.find('.//relative-time').get('datetime')
            if e.get('class') == 'blame-line':
                line = e.xpath(".//td[contains(@class, 'blob-num')]").pop().text
                self.blame_data[int(line)] = blame

    def get_blame_page(self, commit, file):
        blame_url = self.project_link + "/blame/" + commit + file
        response = requests.get(blame_url)
        self._parse_gh_blame_html(respone.content)

    def load_html_file(self, html_path):
        with open(html_path) as f:
            self._parse_gh_blame_html(f.read())

    def print_blame_data(self, attribute):
        print('Length', len(self.blame_data))
        for k, v in self.blame_data.items():
            print(k, v.get(attribute))

    def blame_line(self, line):
        if len(self.blame_data) == 0:
            self.logger.error("HTML not loaded before requesting lines")
            return None
        blame_info = self.blame_data.get(line)
        if not blame_info:
            self.logger.error("No blame information for line {}".format(line))
        return blame_info


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stderr, format='%(name)s %(levelname)s %(message)s')

    blamer = BlameParser(project_link='', logger=log)
    blamer.load_html_file('test_data/test_blame.html')
    blame_info = blamer.blame_line(1)
    print(blame_info)
