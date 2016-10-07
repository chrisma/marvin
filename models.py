#!/usr/bin/env python3

from enum import Enum

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
