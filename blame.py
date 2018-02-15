#!/usr/bin/env python3

import json, sys, logging
from collections import OrderedDict
import requests
from lxml import html
from models import LineBlame

module = sys.modules['__main__'].__file__
log = logging.getLogger(module)

def get_first(lst, default=None):
    return lst[0] if lst else default

class BlameParser:

    def __init__(self, project_link, logger = None):
        self.project_link = project_link
        self.logger = logger or logging
        self.blame_data = OrderedDict()
        self.file_data = OrderedDict()

    def _parse_gh_blame_html(self, string):
        html_tree = html.fromstring(string)
        expression = ".//div[contains(@class, 'blame-container')]"
        container = html_tree.xpath(expression).pop()
        blame = None

        for hunk in container.iterchildren():
            if 'blame-hunk' in hunk.get('class'):
                for e in hunk.iterchildren():
                    # Every <div class="blame-commit">commit info</div> element
                    # is followed by the corresponding lines in a
                    # <div class="width-full">line info</div> element
                    if 'blame-commit' in e.get('class'):
                        blame = LineBlame(*[None]*6)
                        message_anchor = e.xpath(".//a[contains(@class, 'message')]").pop()
                        blame.commit_url = message_anchor.get('href')
                        blame.short_sha = message_anchor.get('href').rsplit('/', 1)[-1]
                        blame.commit_message = message_anchor.get('title')
                        blame.user_name = e.xpath(".//div[contains(@class, 'AvatarStack-body')]").pop().get('aria-label')
                        blame.avatar_url = get_first(e.xpath('.//a[@class="avatar"]/img/@src'))
                        if blame.avatar_url is None:
                            log.info('Avatar for ' + blame.user_name + ' not found')
                        blame.time = e.xpath(".//time-ago").pop().get('datetime')
                    if e.get('class') == 'width-full':
                        # Contains divs containing line number and text
                        for line_element in e.iterchildren():
                            line_number = line_element.xpath(".//div[contains(@class, 'blob-num')]").pop().text
                            self.blame_data[int(line_number)] = blame
                            line_contents = line_element.xpath(".//div[contains(@class, 'blob-code')]").pop().text_content()
                            self.file_data[int(line_number)] = line_contents

    def get_blame_page(self, commit, file):
        blame_url = self.project_link + "/blame/" + commit + "/" + file
        print('Blame URL', blame_url)
        response = requests.get(blame_url)
        self._parse_gh_blame_html(response.content)

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

    blamer.load_html_file('test_data/test_blame_new.html')
    blame_info = blamer.blame_line(1)
    print(blame_info)
