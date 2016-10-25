#!/usr/bin/env python3

from enum import Enum

class LineChange:

    class ChangeType(Enum):
            added = 1
            deleted = 2
            modified = 3

    def __init__(self, number=None, change_type=None, filename=None, commit=None):
        self.number = number
        self.change_type = change_type
        self.filename = filename
        self.commit = commit
        self.author = None

    def __str__(self):
        return ', '.join("{}: {}".format(k, str(v)) for k,v in vars(self).items())

    def __repr__(self):
        return "<{klass} {str}>".format(klass=self.__class__.__name__, str=str(self))
