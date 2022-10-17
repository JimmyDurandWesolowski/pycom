'''Abstract Window interface to define the curses Window class'''

from abc import ABCMeta, abstractmethod
from typing import Tuple

__author__ = 'Jimmy Durand Wesolowski'
__copyright__ = 'Copyright (C) 2022 Jimmy Durand Wesolowski'
__license__ = 'GPL v2.0'
__version__ = '1.0'


class Window:  # pragma: no cover (interface)
    '''Abstract Window interface'''

    __metaclass__ = ABCMeta

    @abstractmethod
    def addstr(self, posy: int, posx: int, line: str) -> None:
        '''Add "line" at the given position "posy" and "posx"'''
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        '''Clear the screen'''
        raise NotImplementedError

    @abstractmethod
    def clrtobot(self) -> None:
        '''Clear from the current position to the bottom of the window'''
        raise NotImplementedError

    @abstractmethod
    def clrtoeol(self) -> None:
        '''Clear from the current position to the end of the line'''
        raise NotImplementedError

    @abstractmethod
    def getch(self) -> int:
        '''Retrieve one character from the standard input'''
        raise NotImplementedError

    @abstractmethod
    def getmaxyx(self) -> Tuple[int, int]:
        '''Get the window dimension as y, x'''
        raise NotImplementedError

    @abstractmethod
    def keypad(self, enable: bool) -> None:
        '''Enable or disable the keypad'''
        raise NotImplementedError

    @abstractmethod
    def move(self, posy: int, posx: int) -> None:
        '''Move the current position to "posy", "posx"'''
        raise NotImplementedError

    @abstractmethod
    def refresh(self) -> None:
        '''Refresh the window'''
        raise NotImplementedError
