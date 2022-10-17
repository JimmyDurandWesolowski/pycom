'''Abstract Terminal interface definition'''

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, List

import pycom.cursorpos
import pycom.history
import pycom.mode

# pylint: disable=duplicate-code
__author__ = 'Jimmy Durand Wesolowski'
__copyright__ = 'Copyright (C) 2022 Jimmy Durand Wesolowski'
__license__ = 'GPL v2.0'
__version__ = '1.0'


if TYPE_CHECKING:
    from pycom.term_win import Interface, TermLine  # pragma: no cover (type)


class Terminal:  # pragma: no cover (interface)
    '''Abstract Terminal interface'''

    __metaclass__ = ABCMeta
    history: pycom.history.History
    interface: 'Interface'
    line_current: 'TermLine'

    @abstractmethod
    def clear(self):
        '''Clear the terminal visible content (not its history)'''
        raise NotImplementedError

    @abstractmethod
    def mode_set(self, mode: pycom.mode.Mode) -> None:
        '''Change the current mode to "mode"'''
        raise NotImplementedError

    @abstractmethod
    def newline(self) -> None:
        '''Enter a new line'''
        raise NotImplementedError

    @abstractmethod
    def overwrite(self, content):
        '''Overwrite the current line'''
        raise NotImplementedError

    @abstractmethod
    def pos_update(self, pos: pycom.cursorpos.CursorPos) -> None:
        '''Update the line position'''
        raise NotImplementedError

    @abstractmethod
    def read(self) -> None:
        '''Read the given terminal input'''
        raise NotImplementedError

    @abstractmethod
    def reset(self):
        '''Reset the terminal, clearing the content and history'''
        raise NotImplementedError

    @abstractmethod
    def terminate(self) -> None:
        '''Terminate the terminal'''
        raise NotImplementedError

    @abstractmethod
    def update(self):
        '''Update the terminal display, requirede to reflect changes'''
        raise NotImplementedError

    @abstractmethod
    def write(self, lines: List[str]):
        '''Write "lines" to the terminal'''
        raise NotImplementedError
