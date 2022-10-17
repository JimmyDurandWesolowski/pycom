'''Terminal operation mode type implementation'''

import enum

__author__ = 'Jimmy Durand Wesolowski'
__copyright__ = 'Copyright (C) 2022 Jimmy Durand Wesolowski'
__license__ = 'GPL v2.0'
__version__ = '1.0'


class Mode(enum.Enum):
    '''Terminal operation mode type enumeration class'''
    NORMAL = 0
    COMPLETION = 1
    ESCAPE = 2
    HISTORY = 3
    SEARCH = 4
    ANY = -1
