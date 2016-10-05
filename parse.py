#!/bin/usr/python

import argparse
import re

def find_modified_lines(added_lines, removed_lines):
    modified_lines = {}

    for key in set(removed_lines.keys()).intersection(set(added_lines.keys())):    
        modified_lines[key] = removed_lines[key] + " -> " + added_lines[key]
        del added_lines[key]
        del removed_lines[key]

    return added_lines, removed_lines, modified_lines

def parse_file(filename):
    print('Parsing: ', filename)

    with open(filename) as f:
        lines = f.readlines()
        diff_start_re = re.compile('^@@ -([0-9]+),([0-9]+) \+([0-9]+),([0-9]+) @@.*$')
        diff_filename_re = re.compile('^diff --git (.*)$')
        diff_end_re = re.compile('^From [a-f,0-9]{40} [A-Z][a-z]{2} [A-Z][a-z]{2} [0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} [0-9]{4}$')

        current_file = None
        added_lines = {}
        removed_lines = {}

        for idx in range(len(lines)):
            line = lines[idx]
            
            filename_match = diff_filename_re.match(line)
            if filename_match != None:
                if current_file != None:
                    added_lines, removed_lines, modified_lines = find_modified_lines(added_lines, removed_lines)

                    print("added", len(added_lines))
                    print("removed", len(removed_lines))
                    print("modified", len(modified_lines))
                    added_lines = {}
                    removed_lines = {}

                current_file = filename_match.group(1)
                print("Current file set to", current_file)
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
            while idx < len(lines) and diff_start_re.match(lines[idx]) == None and diff_end_re.match(lines[idx]) == None and diff_filename_re.match(lines[idx]) == None:

                line = lines[idx]

                if line.startswith("+"):
                    after_line += 1
                #    print("new line", after_line, "was added", line)
                    added_lines[after_line] = line

                elif line.startswith("-"):
                    before_line += 1
                #    print("old line", before_line, "was deleted", line)
                    removed_lines[before_line] = line
                else:
                    before_line += 1
                    after_line += 1

                idx += 1

            if not (after_finish == after_line and before_finish == before_line):
                print("Something went wrong with selecting the lines", after_line, "vs", after_finish, before_line, "vs", before_finish)

        if current_file != None:
            added_lines, removed_lines, modified_lines = find_modified_lines(added_lines, removed_lines)

            print("added", len(added_lines))
            print("removed", len(removed_lines))
            print("modified", len(modified_lines))

def main():
    parser = argparse.ArgumentParser(description='Parses a diff, returns changed lines')
    parser.add_argument('diff', type=str, help='the filename of the diff to parse')

    args = parser.parse_args()
    parse_file(args.diff)

if __name__ == "__main__":
    main()