#!/usr/bin/env python3

import argparse
import logging
import sys
import requests
from collections import OrderedDict

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
        self.additional_lines = OrderedDict()
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

    def load_blame_from_html(self, file, commit_sha, filepath):
        if not file in self.blame_data:
            self.blame_data[file] = {}

        self.blame_data[file][commit_sha] = BlameParser(self.project_link)
        self.blame_data[file][commit_sha].load_html_file(filepath)

    def blame_lines(self):
        for file in self.diff_parser.changes.keys():
            if not file in self.blame_data:
                self.blame_data[file] = {}

            for i in range(3):
                for line, linechange in self.diff_parser.changes[file][i].items():
                    if not linechange.commit_sha in self.blame_data[file]:
                        self.blame_data[file][linechange.commit_sha] = BlameParser(self.project_link)
                        # TODO!! Do the line blaming for removed lines differently
                        self.blame_data[file][linechange.commit_sha].get_blame_page(linechange.commit_sha, file)
                    
                    linechange.author = self.blame_data[file][linechange.commit_sha].blame_line(line)

    def is_interesting(self, line):
        to_skip = set(["", "{", "}", "begin", "end"])

        return not line.strip() in to_skip

    def has_been_changed(self, line_n, file, commit):
        for i in range(3):
            if line_n in self.diff_parser.changes[file][i] and \
                self.diff_parser.changes[file][i][line_n].commit_sha == commit:
                return True

        return False

    def _find_intersing_line(self, file, line_n, linechange, offset, step):
        p = offset
        while not self.has_been_changed(line_n + p, file, linechange.commit_sha) and \
            not self.is_interesting(self.blame_data[file][linechange.commit_sha].file_data[line_n + p]):
            p += step

            if line_n + p < 1 or line_n + p > len(self.blame_data[file][linechange.commit_sha].file_data):
                return None

        if not self.has_been_changed(line_n + p, file, linechange.commit_sha):
            return LineChange(line_n + p, LineChange.ChangeType.interesting, file, linechange.commit_sha)
        else:
            return None

    def _find_previous_intersing_line(self, file, line_n, linechange):
        return self._find_intersing_line(file, line_n, linechange, -1, -1)

    def _find_next_intersing_line(self, file, line_n, linechange):
        return self._find_intersing_line(file, line_n, linechange, 1, 1)

    def load_additional_lines(self):
        for file in self.diff_parser.changes.keys():
            for i in range(3):
                for line_n, linechange in self.diff_parser.changes[file][i].items():
                    prev_line = self._find_previous_intersing_line(file, line_n, linechange)
                    next_line = self._find_next_intersing_line(file, line_n, linechange)
                    
                    if prev_line != None:
                        self.additional_lines[prev_line.line_number] = prev_line
                    if next_line != None:
                        self.additional_lines[next_line.line_number] = next_line

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

