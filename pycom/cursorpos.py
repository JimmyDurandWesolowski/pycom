'''Cursor type implementation'''

from enum import Enum

__author__ = 'Jimmy Durand Wesolowski'
__copyright__ = 'Copyright (C) 2022 Jimmy Durand Wesolowski'
__license__ = 'GPL v2.0'
__version__ = '1.0'


class CursorPos(Enum):
    '''Cursor type enumeration class'''
    HOME = 1
    END = 2
    LEFT = 3
    RIGHT = 4
