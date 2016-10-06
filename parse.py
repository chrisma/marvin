#!/bin/usr/python


from lxml import html
from enum import Enum
import argparse
import re
import requests

def load_blame_page(commit, file):
    blame_url = "https://github.com/hpi-swt2/wimi-portal/blame/" + commit + file
    page = requests.get(blame_url)

    html_tree = html.fromstring(page.content)
    return html_tree


class LineChange:

    class ChangeType(Enum):
            added = 1
            deleted = 2
            modified = 3


    def __init__(self):
        self.number = None
        self.change_type = None
        self.author = None
        self.filename = None
        self.commit = None

    def __init__(self, number, change_type, filename, commit):
        self.number = number
        self.change_type = change_type
        self.filename = filename
        self.commit = commit


def calc_modified_lines(added_lines, removed_lines):
    modified_lines = {}

    for key in set(removed_lines.keys()).intersection(set(added_lines.keys())):    
        modified_lines[key] = LineChange(key, LineChange.ChangeType.modified, added_lines[key].filename, added_lines[key].commit)
        del added_lines[key]
        del removed_lines[key]

    return added_lines, removed_lines, modified_lines

def load_file(filename):
    print('Parsing: ', filename)

    with open(filename) as f:
        return f.readlines()

def parse_lines(lines):
    diff_start_re = re.compile('^@@ -([0-9]+),([0-9]+) \+([0-9]+),([0-9]+) @@.*$')
    diff_long_commit_re = re.compile('^From ([a-f,0-9]{40}) [A-Z][a-z]{2} [A-Z][a-z]{2} [0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} [0-9]{4}$')
    diff_filename_re = re.compile('^diff --git (.*?) (.*?)$')
    diff_commits_re = re.compile('^index ([a-f,0-9]{7})\.\.([a-f,0-9]{7}).*$')

    blame_file = None
    current_file = None
    current_before_commit = None
    current_after_commit = None

    processed_lines = []

    added_lines = {}
    removed_lines = {}

    for idx in range(len(lines)):
        line = lines[idx]
        
        commit_match = diff_long_commit_re.match(line)
        if commit_match != None:
            continue

        filename_match = diff_filename_re.match(line)
        if filename_match != None:
            if current_file != None:
                added_lines, removed_lines, modified_lines = calc_modified_lines(added_lines, removed_lines)

                # print("added", len(added_lines))
                # print("removed", len(removed_lines))
                # print("modified", len(modified_lines))
                processed_lines += list(added_lines.values()) + list(removed_lines.values()) + list(modified_lines.values())

                # blame lines
                # if blame_file != None:
                added_lines = {}
                removed_lines = {}

            current_file = filename_match.group(2)
            print("Current file set to", current_file)

            # Load short commit
            idx += 1
            line = lines[idx]
            
            commits_match = diff_commits_re.match(line)
            if commits_match != None:
                current_before_commit = commits_match.group(1)
                current_after_commit = commits_match.group(2)
            else:
                print("[Error] Something went wrong when parsing commit!")

            # blame_file = load_blame_page(current_commit, current_file)

            continue

        res = diff_start_re.match(line)

        if res == None:
            continue

        before_line = int(res.group(1))
        before_offset = int(res.group(2))
        after_line = int(res.group(3))
        after_offset = int(res.group(4))

        before_finish = before_line + before_offset
        after_finish = after_line + after_offset

        idx += 1

        # ananalyse individual change
        while idx < len(lines) and diff_start_re.match(lines[idx]) == None and diff_long_commit_re.match(lines[idx]) == None and diff_filename_re.match(lines[idx]) == None:

            line = lines[idx]

            if line.startswith("+"):
                after_line += 1
                added_lines[after_line] = LineChange(line, LineChange.ChangeType.added, current_file, current_after_commit)

            elif line.startswith("-"):
                before_line += 1
                removed_lines[before_line] = LineChange(line, LineChange.ChangeType.deleted, current_file, current_before_commit)
            else:
                before_line += 1
                after_line += 1

            idx += 1

        if not (after_finish == after_line and before_finish == before_line):
            print("Something went wrong with parsing the lines", idx, after_line, after_finish, line, lines[idx], lines[idx-1])

    if current_file != None:
        added_lines, removed_lines, modified_lines = calc_modified_lines(added_lines, removed_lines)
        processed_lines += list(added_lines.values()) + list(removed_lines.values()) + list(modified_lines.values())

    return processed_lines

def main():
    parser = argparse.ArgumentParser(description='Parses a diff, returns changed lines')
    parser.add_argument('diff', type=str, help='the filename of the diff to parse')

    args = parser.parse_args()
    parse_lines(load_file(args.diff))

if __name__ == "__main__":
    main()