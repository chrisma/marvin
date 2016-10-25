#!/usr/bin/env python3

from enum import Enum

class LineChange:

    class ChangeType(Enum):
        added = 1
        deleted = 2
        modified = 3

    def __init__(self, line_number=None, change_type=None, file_path=None, commit_sha=None):
        self.line_number = line_number
        self.change_type = change_type
        self.file_path = file_path
        self.commit_sha = commit_sha
        self.author = None

    def __str__(self):
        return ', '.join("{}: {}".format(k, str(v)) for k,v in vars(self).items())

    def __repr__(self):
        return "<{klass} {str}>".format(klass=self.__class__.__name__, str=str(self))

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)