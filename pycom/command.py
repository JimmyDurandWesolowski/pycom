'''Terminal command implementation to react to the different command keys
according to the current terminal operation mode
'''

import curses
import curses.ascii
import logging
from typing import Callable, Dict, NewType

import pycom.terminal
import pycom.utils
from pycom.mode import Mode

__author__ = 'Jimmy Durand Wesolowski'
__copyright__ = 'Copyright (C) 2022 Jimmy Durand Wesolowski'
__license__ = 'GPL v2.0'
__version__ = '1.0'


TypeKey = NewType('TypeKey', int)


class Command:
    '''Normal mode and base command class'''

    KEYMAP_CURSOR = {
        curses.KEY_LEFT: pycom.cursorpos.CursorPos.LEFT,
        curses.KEY_RIGHT: pycom.cursorpos.CursorPos.RIGHT,
        curses.KEY_HOME: pycom.cursorpos.CursorPos.HOME,
        curses.KEY_END: pycom.cursorpos.CursorPos.END
    }

    MAP_MODE: Dict[int, Mode] = {
        curses.ascii.BEL: Mode.NORMAL,
        curses.ascii.HT: Mode.COMPLETION,
        curses.ascii.TAB: Mode.COMPLETION,
        curses.ascii.DC2: Mode.SEARCH,
        curses.ascii.ESC: Mode.ESCAPE,
        curses.KEY_UP: Mode.HISTORY,
    }

    def __init__(self, terminal: pycom.terminal.Terminal):
        self.interface = terminal.interface
        self.mode_idx: int = 0
        self.logger: logging.Logger = logging.getLogger(
            self.__class__.__name__)
        self.terminal: pycom.terminal.Terminal = terminal
        self._map: Dict[int, Callable[[int], bool]] = {
            curses.ascii.BEL: self.mode_set,
            curses.ascii.EOT: self.eot,
            curses.ascii.CR: self.newline,
            curses.ascii.NL: self.newline,
            # curses.ascii.HT: self.mode_set,
            # curses.ascii.TAB: self.mode_set,
            # curses.ascii.DC2: self.mode_set,
            # curses.ascii.ESC: self.mode_set,
            curses.KEY_BACKSPACE: self.backspace,
            curses.KEY_DOWN: self.noop,
            curses.KEY_END: self.line_position,
            curses.KEY_HOME: self.line_position,
            curses.KEY_LEFT: self.line_position,
            curses.KEY_RIGHT: self.line_position,
            curses.KEY_UP: self.mode_set,
        }

    def __call__(self, key: int) -> bool:
        ret = True
        if not curses.ascii.iscntrl(key) and not curses.ascii.ismeta(key):
            self.terminal.line_current += chr(key)
            return ret
        try:
            name = f'{pycom.utils.ASCII_MAP[key]} ({key})'
        except KeyError:
            name = str(key)
        try:
            func = self._map[key]
        except KeyError:
            self.interface.write(
                'error', f'Line functionality {name} not implemented yet')
            self.logger.warning('Command %s not implemented', key)
            return False
        self.logger.debug('Processing command: %s - %s', name, func.__name__)
        if not func(key):
            self.interface.write(
                'error',
                f'Line functionality {name} not fully implemented yet')
            self.logger.warning('Command %s not fully implemented', key)
            ret = False
        return ret

    def _mode_update(self, mode: Mode):
        self.terminal.mode_set(mode)

    def backspace(self, key: int) -> bool:
        '''Backspace key action'''
        # pylint: disable=unused-argument
        self.terminal.line_current.delete(1)
        return True

    def eot(self, key: int) -> bool:
        '''End of transmission / CTRL+D key action'''
        # pylint: disable=unused-argument
        self.terminal.terminate()
        return True

    def line_position(self, key: int) -> bool:
        '''Line position action based on the KEYMAP_CURSOR'''
        self.terminal.pos_update(self.KEYMAP_CURSOR[key])
        return True

    def mode_set(self, key: int) -> bool:
        '''Change the current mode of operation'''
        self._mode_update(self.MAP_MODE[key])
        return True

    def newline(self, key: int) -> bool:
        '''New line validation action'''
        # pylint: disable=unused-argument
        self.terminal.newline()
        self._mode_update(Mode.NORMAL)
        return True

    def noop(self, key: int) -> bool:
        '''No operation'''
        # pylint: disable=unused-argument,no-self-use
        return True

    def start(self):
        '''Start the current command mode'''

    def stop(self):
        '''Stop the current command mode'''


class CommandHistory(Command):
    '''Command class when operating in "history" mode'''

    def __init__(self, terminal: pycom.terminal.Terminal):
        super().__init__(terminal)
        self._map.update({
            curses.KEY_DOWN: self.history_next,
            curses.KEY_UP: self.history_prev,
        })

    def __call__(self, key: int) -> bool:
        if not curses.ascii.iscntrl(key) and not curses.ascii.ismeta(key):
            # The line needs to be copied not to modify in place
            line = str(self.terminal.history[self.terminal.history.pos])
            line += chr(key)
            self.terminal.overwrite(line)
            self._mode_update(Mode.NORMAL)
            return True
        try:
            func = self._map[key]
        except KeyError:
            return False
        return func(key)

    def backspace(self, key: int) -> bool:
        # pylint: disable=unused-argument
        line = str(self.terminal.history.line_current)
        self.terminal.overwrite(line)
        self.terminal.line_current.delete(1)
        self._mode_update(Mode.NORMAL)
        return True

    def history_next(self, key: int) -> bool:
        '''Get the next item in history'''
        # pylint: disable=unused-argument
        self.logger.debug('Next history entry')
        if not self.terminal.history.pos_update(1):
            self._mode_update(Mode.NORMAL)
        return True

    def history_prev(self, key: int) -> bool:
        '''Get the previous item in history'''
        # pylint: disable=unused-argument
        self.logger.debug('Previous history entry')
        if not self.terminal.history.pos_update(-1):
            self._mode_update(Mode.NORMAL)
        return True

    def newline(self, key: int) -> bool:
        # pylint: disable=unused-argument
        line = str(self.terminal.history.line_current)
        self.terminal.history.reset()
        self.terminal.overwrite(line)
        self._mode_update(Mode.NORMAL)
        return True

    def start(self):
        self.terminal.history.reset()


# class CommandSearch(Command):
#     def __call__(self, key: int) -> bool:
#         if not curses.ascii.iscntrl(key) and not curses.ascii.ismeta(key):
#             self.terminal.search(key)
#             return True
#         try:
#             func = self._map[key]
#         except KeyError:
#             return False
#         return func(key)

#     def search(self, key: int) -> bool:
#         self.terminal.search.next()

#     def start(self):
#         self.terminal.search.reset()
