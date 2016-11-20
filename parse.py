#!/usr/bin/env python3

import argparse
import sys
import re
import logging

from models import LineChange
from blame import BlameParser

module = sys.modules['__main__'].__file__
log = logging.getLogger(module)

class DiffParser:

    def __init__(self, filename):
        self.load_file(filename)
        self.changes = {}
        self.interesting = {}
        self.added_files = set([])
        self.removed_files = set([])

    def eof(self):
        return self.line_idx >= len(self.lines)

    def load_file(self, filename):
        log.debug("Parsing {}".format(filename))

        with open(filename) as f:
            self.lines = f.readlines()
            self.line_idx = 0

    def parse_short_commit_hash(self):
        diff_commits_re = re.compile('^index ([a-f,0-9]{7})\.\.([a-f,0-9]{7}).*$')
        new_file_re = re.compile('^new file mode [0-9]{6}$')
        delete_file_re = re.compile('^deleted file mode [0-9]{6}$')

        line = self.lines[self.line_idx]

        if new_file_re.match(line) != None:
            self.added_files.add(self.current_file)

        elif delete_file_re.match(line) != None:
            self.removed_files.add(self.current_file)

        if new_file_re.match(line) != None or delete_file_re.match(line) != None:
            self.line_idx += 1
            line = self.lines[self.line_idx]

        commits_match = diff_commits_re.match(line)
        if commits_match != None:
            self.from_commit = commits_match.group(1)
            self.to_commit  = commits_match.group(2)
        else:
            log.error("Something went wrong when parsing commit!")


    def evaluate_line(self, line):
        to_skip = set(["", "{", "}", "begin", "end"])

        return not line.strip() in to_skip

    def parse_next_commit(self, added, removed, modified, interesting):
        if self.eof():
            return None

        commit_re = re.compile('^@@ -([0-9]+),([0-9]+) \+([0-9]+),([0-9]+) @@.*$')
        filename_re = re.compile('^diff --git a/(.*?) b/(.*?)$')
        long_re = re.compile('^From ([a-f,0-9]{40}) [A-Z][a-z]{2} [A-Z][a-z]{2} [0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} [0-9]{4}$')
    
        match = None

        while not self.eof() and match == None:
            match = commit_re.match(self.lines[self.line_idx])
            self.line_idx += 1

        if match == None:
            return None

        before_line_n = int(match.group(1))
        before_offset = int(match.group(2))
        after_line_n = int(match.group(3))
        after_offset = int(match.group(4))

        before_finish_line_n = before_line_n + before_offset
        after_finish_line_n = after_line_n + after_offset
        
        removed_in_new_file = {}

        while not self.eof():
            line = self.lines[self.line_idx]

            match = commit_re.match(line)
            if match != None:
                break
            match = filename_re.match(line)
            if match != None:
                break
            match = long_re.match(line)
            if match != None:
                break

            if line.startswith("+"):
                if after_line_n in removed_in_new_file and len(removed_in_new_file[after_line_n]) > 0:
                    del removed[removed_in_new_file[after_line_n].pop()]
                    modified[after_line_n] = LineChange(after_line_n, LineChange.ChangeType.modified, self.current_file, self.to_commit)
                else:
                    added[after_line_n] = LineChange(after_line_n, LineChange.ChangeType.added, self.current_file, self.to_commit)
                
                after_line_n += 1

            elif line.startswith("-"):
                if after_line_n in added:
                    del added[after_line_n]
                    modified[after_line_n] = LineChange(after_line_n, LineChange.ChangeType.modified, self.current_file, self.to_commit)
                else:
                    removed[before_line_n] = LineChange(before_line_n, LineChange.ChangeType.deleted, self.current_file, self.from_commit)
                    if not after_line_n in removed_in_new_file:
                        removed_in_new_file[after_line_n] = []
                    removed_in_new_file[after_line_n].append(before_line_n)

                before_line_n += 1

            else:
                # TODO find code blocks and better evaluation
                if self.evaluate_line(line):
                    interesting[after_line_n] = LineChange(after_line_n, LineChange.ChangeType.interesting, self.current_file, self.to_commit)

                before_line_n += 1
                after_line_n += 1

            self.line_idx += 1

        if not (after_finish_line_n == after_line_n and before_finish_line_n == before_line_n) \
            and not self.current_file in self.removed_files and not self.current_file in self.added_files:
            log.warning("Something went wrong with parsing commits in {} {}...{} S {} {} B {} v {} A {} v {}".format(
                self.current_file, self.from_commit, self.to_commit, before_finish_line_n - before_offset, after_finish_line_n - after_offset, before_finish_line_n, before_line_n, after_finish_line_n, after_line_n))

    def parse_next_file_changes(self):
        if self.eof():
            return None

        filename_re = re.compile('^diff --git a/(.*?) b/(.*?)$')
        self.current_file = None
        self.to_commit = None
        self.from_commit = None

        match = None

        while not self.eof() and match == None:
            match = filename_re.match(self.lines[self.line_idx])
            self.line_idx += 1

        if match == None:
            return None

        self.current_file = match.group(2)
        log.debug("Current file set to {} ".format(self.current_file))
        added, removed, modified, interesting = {}, {}, {}, {}

        self.parse_short_commit_hash()
        if self.to_commit == None or self.from_commit == None:
            log.error("Failure loading commits for {} from '{}'".format(self.current_file, self.lines[self.line_idx]))
            return None

        self.line_idx += 1

        while not self.eof():
            match = filename_re.match(self.lines[self.line_idx])  
            if match != None:
                break

            self.parse_next_commit(added, removed, modified, interesting)

        self.changes[self.current_file] = added, removed, modified
        self.interesting[self.current_file] = interesting

        self.current_file = None
        self.to_commit = None
        self.from_commit = None

        return True

    def get_all_changes(self):
        changes = []
        for file in self.changes:        
            changes += list(self.changes[file][0].values()) + \
                        list(self.changes[file][1].values()) + \
                        list(self.changes[file][2].values())

        return changes


    def parse(self):

        while not self.eof() and self.parse_next_file_changes():
            pass

        return self.get_all_changes()

def main():
    parser = argparse.ArgumentParser(description='Parses a diff, returns changed lines')
    parser.add_argument('diff', type=str, help='the filename of the diff to parse')
    parser.add_argument('-v', '--verbose', action='count', default=0, help="increases log verbosity for each occurence.")

    args = parser.parse_args()
    log.setLevel([logging.WARNING, logging.INFO, logging.DEBUG][min(2,args.verbose)])

    parser = DiffParser(args.diff)

    log.info("{}".format(parser.parse()))


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stderr, format='%(name)s %(levelname)s %(message)s')
    main()
