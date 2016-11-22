#!/usr/bin/env python3

import argparse
import logging
import sys
import requests

from models import LineChange
from blame import BlameParser
from parse import DiffParser

module = sys.modules['__main__'].__file__
log = logging.getLogger(module)

class Marvin:

    def __init__(self, project_link, pr_n):
        self.project_link = project_link
        self.pr_n = pr_n

        self.raw_diff = None
        self.diff_parser = None
        self.blame = None
        self.blame_data = {}

    def load_diff_from_project(self):
        diff_url = self.project_link + "/pull/" + str(self.pr_n) + ".patch"
        response = requests.get(diff_url)
        self.raw_diff = response.text.split('\n')

    def load_diff_from_filename(self, filename):
        with open(filename) as f:
            self.raw_diff = f.readlines()

    def parse_diff(self):
        self.diff_parser = DiffParser(diff_content=self.raw_diff)
        self.diff_parser.parse()

    def blame_lines(self):
        for file in self.diff_parser.changes.keys():
            self.blame_data[file] = {}

            for line, linechange in self.diff_parser.changes[file][0].items():
                if not linechange.commit_sha in self.blame_data[file]:
                    self.blame_data[file][linechange.commit_sha] = BlameParser(self.project_link).get_blame_page(linechange.commit_sha, file)
                linechange.author = self.blame_data[file][linechange.commit_sha].blame_line(line)
                self.diff_parser.changes[file][0][line] = linechange

def main():
    parser = argparse.ArgumentParser(description='Parses a commit, returns recommendation for reviewer')
    parser.add_argument('project_link', type=str, help='the link to the project')
    parser.add_argument('pr_n', type=int, help='the number of the PR to parse')
    parser.add_argument('-v', '--verbose', action='count', default=0, help="increases log verbosity for each occurence.")

    args = parser.parse_args()
    log.setLevel([logging.WARNING, logging.INFO, logging.DEBUG][min(2,args.verbose)])

    marvin = Marvin(args.project_link, args.pr_n)
    marvin.load_diff_from_project()
    marvin.parse_diff()
    marvin.blame_lines()

    print(marvin.diff_parser.changes)

    log.info("{}".format(marvin.diff_parser.changes))

if __name__ == "__main__":
    logging.basicConfig(stream=sys.stderr, format='%(name)s %(levelname)s %(message)s')
    main()

