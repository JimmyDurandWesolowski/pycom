'''Handling of the curses interface, windows, and line displaying'''
import collections
import curses
import logging
import os
import queue
from typing import Dict, Iterable, List, Optional, SupportsIndex, Tuple, Union

import pycom.config
from pycom.cursorpos import CursorPos
import pycom.terminal
import pycom.utils
import pycom.window

__author__ = 'Jimmy Durand Wesolowski'
__copyright__ = 'Copyright (C) 2022 Jimmy Durand Wesolowski'
__license__ = 'GPL v2.0'
__version__ = '1.0'


ScreenPos = Tuple[int, int]
OptionalTermlines = Optional[
    Union[str, List[str], 'TermLine', List['TermLine'],
          List[Union['TermLine', str]]]
]
Window = Union[pycom.window.Window, 'curses._CursesWindow']


class TermLine:
    '''Basic implemtation of a window editable line'''
    __slots__ = (
        '_content', 'attr', 'logger', 'num', 'pos',
        'prompt', 'window_cols', 'window_lines'
    )

    PROMPT_FMT = 'line {:5}: '

    def __init__(self, window_lines: int, window_cols: int,
                 content: Optional[str] = None):
        self._content: str = content if content is not None else ''
        if not isinstance(self._content, str):
            raise AssertionError
        self.attr: int = 0
        self.window_cols: int = window_cols
        self.window_lines: int = window_lines
        self.logger: logging.Logger = logging.getLogger(
            self.__class__.__name__)
        self.pos: int = len(self._content)
        self.prompt: str = ''

    def __add__(self, content: Union[str, 'TermLine']):
        start, end = self._content[:self.pos], self._content[self.pos:]
        self._content = start + str(content) + end
        self.pos += len(content)
        return self

    def __contains__(self, content: Union[str, 'TermLine']):
        if isinstance(content, TermLine):
            return content._content in self._content
        return content in self._content

    def __eq__(self, termline):
        try:
            if not isinstance(self._content, str):
                raise AssertionError
            return self._content == termline._content
        except AttributeError as exc:
            if not isinstance(termline, str):
                raise AssertionError from exc
            return self._content == termline

    def __hash__(self):
        return hash(self._content)

    def __getitem__(self, idx: Union[SupportsIndex, slice]):
        return self._content[idx]

    def __len__(self):
        return len(self._content)

    def __repr__(self):
        if self._content:
            content = self._content
            if len(content) > 57:
                content = f'{content[len(content) - 57:]}...'
            return (f'[{self.__class__.__name__} {len(self.content)} line(s) '
                    f'"{content}"]')
        return f'[{self.__class__.__name__} empty]'

    def __str__(self):
        return self._content

    def _update_pos(self, pos: int) -> ScreenPos:
        if pos < 0:
            self.pos = max(0, self.pos + pos)
        elif pos > 0:
            self.pos = min(self.pos + pos, len(self._content))
        return self.screen_pos

    def bold(self) -> None:
        '''Makes the line bold'''
        self.attr |= curses.A_BOLD

    @property
    def content(self) -> List[str]:
        '''Returns the line content split according to the available space'''
        if not isinstance(self._content, str):
            raise AssertionError
        if self.pos < 0 or self.pos > len(self._content + self.prompt):
            raise AssertionError
        return list(
            pycom.utils.chunks(self.prompt + self._content, self.window_cols))

    def delete(self, num: int = 1) -> ScreenPos:
        '''Deletes up to "num" character before the current position in the
        line and returns the new position in the line
        '''
        self.logger.debug('Deleting %d character from pos %d', num, self.pos)
        if num > len(self._content):
            num = len(self._content)
        self._content = (self._content[:self.pos - num]
                         + self._content[self.pos:])
        if not isinstance(self._content, str):
            raise AssertionError
        return self._update_pos(-num)

    def get(self, maximum: Optional[int] = None) -> List[str]:
        '''Returns the line content split according to the available space, up
        to the number of lines available in the window, or the given "maximum"
        argument
        '''
        if maximum is None:
            maximum = self.window_lines
        start = max(0, len(self.content) - maximum)
        return self.content[start:]

    def highlight(self):
        '''Highlight the line'''
        self.attr |= curses.A_REVERSE

    def normal(self):
        '''Return the line to its default style value'''
        self.attr = curses.A_NORMAL

    def prompt_set(self, num: int = 0) -> None:
        '''Set the prompt to the given index (default 0) using the
        "PROMPT_FMT"'''
        self.prompt = self.PROMPT_FMT.format(num)

    @property
    def screen_pos(self) -> ScreenPos:
        '''Returns the position of the line according to the window
        restrictions
        '''
        pos = self.pos + len(self.prompt)
        return (pos // self.window_cols, pos % self.window_cols)

    def split(self, *args, **kwargs):
        '''Perform a "split" on the line content'''
        return self._content.split(*args, **kwargs)

    def rsplit(self, *args, **kwargs):
        '''Perform a "rsplit" on the line content'''
        return self._content.rsplit(*args, **kwargs)

    def update_pos(self,
                   pos: Union[CursorPos, int]) -> ScreenPos:
        '''Update the position in the line'''
        self.logger.debug('Moving cursor at %s', pos)
        if isinstance(pos, int):
            return self._update_pos(pos)

        if pos == CursorPos.HOME:
            self.pos = 0
            return self.screen_pos
        if pos == CursorPos.END:
            self.pos = len(self._content)
            return self.screen_pos
        if pos == CursorPos.LEFT:
            return self._update_pos(-1)
        if pos == CursorPos.RIGHT:
            return self._update_pos(1)
        raise AssertionError(f'Unknown position {pos}')

    def write(self, content: str) -> ScreenPos:
        '''Write additional content in the line, adding at the current
        position, and moving the current position accordingly
        '''
        self._content = (self._content[:self.pos] + content
                         + self._content[self.pos:])
        if not isinstance(self._content, str):
            raise AssertionError
        return self._update_pos(len(content))


class TermWindow:
    '''Terminal window implementation using curses'''

    __slots__ = [
        '_title', 'content', 'cursor', 'dim', 'logger',
        'name', 'position', 'posx', 'posy', 'prompt',
        'queue', 'window'
    ]

    # pylint: disable=too-many-arguments
    def __init__(self, name: str, lines: int, cols: int, posy: int, posx: int):
        self.content = None
        self.cursor: bool = False
        self.dim = (lines, cols)
        self.queue: queue.Queue
        self.name: str = name
        self.position: Optional[Tuple[int, int]] = (0, 0)
        self.prompt: bool = False
        self._title: Optional[TermLine] = None
        # pylint: disable=no-member
        self.window: Window = curses.newwin(lines, cols, posy, posx)
        self.logger = logging.getLogger(
            f'{self.__class__.__name__} {self.name}')
        self.logger.debug('%s window: %dx%d@%dx%d', self.name, *self.dim,
                          *self.window.getbegyx())
        self.queue = queue.Queue()
        self.window.keypad(True)
        self.window.move(0, 0)

    def _sanitize(self, lines: OptionalTermlines = None) -> List[TermLine]:
        if lines is None:
            return []
        items: Iterable
        if isinstance(lines, (List, collections.UserList)):
            items = lines
        else:
            items = [lines]
        termlines = []
        for line in items:
            if not isinstance(line, TermLine):
                termlines.append(self.line_create(line))
            else:
                termlines.append(line)
        return termlines

    def clear(self) -> None:
        '''Clear the terminal display'''
        self.logger.debug('Clearing')
        self.window.clear()
        self.write()

    def cursor_enable(self, status: bool = True) -> None:
        '''Enable or disable the cursor according to "status"'''
        self.cursor = status
        if status:
            curses.curs_set(1)
        else:
            curses.curs_set(0)

    def line_create(self, line: Optional[Union[str, TermLine]] = None,
                    num: int = 1,
                    prompt: Optional[str] = None) -> TermLine:
        '''Create a new line in the window based on the window properties,
        indexing it from "num", and allowing to set its prompt to "prompt"
        '''
        if line is None:
            line = ''
        termline = TermLine(*self.dim, content=str(line))
        if self.prompt:
            termline.prompt_set(num)
        if prompt is not None:
            termline.prompt = prompt
        return termline

    def lines_get(self, lines: List[str], num_start: int = 1):
        '''Create new lines in the window based on the window properties,
        starting their indexing from "num_start"
        '''
        return [self.line_create(line, num=idx + num_start)
                for idx, line in enumerate(lines)]

    def prompt_enable(self, enable: bool = True):
        '''Enable or disable a prompt for this window according to "enable"'''
        self.prompt = enable

    def read(self):
        '''Read from the terminal window'''
        return self.window.getch()

    def redraw(self) -> None:
        '''Redraw the current window. Required to display the newly written
        lines with "write"
        '''
        self.logger.info('Redrawing (%d)', self.queue.qsize())
        if self.queue.qsize():
            while True:
                try:
                    self.content, self.position = self.queue.get_nowait()
                except queue.Empty:
                    break
        self.logger.debug('Redrawing %s, %s', self.content, self.position)
        posy = 0
        curx = 0
        if self.content is not None:
            for termline, screenlines in reversed(self.content):
                for line in screenlines:
                    self.logger.debug('Writing %dx%d: %s', posy, 0, line)
                    try:
                        self.window.addstr(posy, 0, line, termline.attr)
                    except (curses.error, ValueError) as exc:
                        self.logger.warning('Failed to write "%s" at %d: %s',
                                            line, posy, exc)
                    self.window.clrtoeol()
                    posy += 1
                _, curx = termline.screen_pos
        self.position = (posy - 1, curx)
        if self.cursor:
            self.logger.debug('Setting cursor')
            self.window.move(*self.position)
        self.window.refresh()
        self.window.clrtobot()

    def title_set(self, title: str) -> None:
        '''Set the window title to "title"'''
        self._title = self.line_create(title[:self.dim[1]], prompt='')
        self._title.bold()

    def write(self, lines: OptionalTermlines = None,
              position: Tuple[int, int] = None) -> None:
        '''Write the given lines in the window, at "position" if given, or from
        the top left of the window otherwise
        '''
        self.logger.info('Writing')
        termlines = self._sanitize(lines)
        quota = self.dim[0]
        if self._title is not None:
            quota -= 1
        else:
            self.logger.debug('No title set')
        if termlines is not None:
            self.logger.debug('Updating %s%s%s', self._title, os.linesep,
                              os.linesep.join([f'  "{line}"'
                                               for line in termlines]))
        else:
            self.logger.debug('Updating %s', self._title)
        content = []
        if termlines is not None:
            for termline in reversed(termlines):
                screenlines = termline.get(maximum=quota)
                quota -= len(screenlines)
                content.append((termline, screenlines))
                if not quota:
                    self.logger.info('Window full, clearing')
                    self.clear()
                    break
        if self._title is not None:
            content += [(self._title, self._title.get())]
        self.queue.put((content, position))


# pylint: disable=too-many-instance-attributes
class Interface:
    '''Interface implementation to display the curses windows based on the
    given configuration
    '''

    def __init__(self, config: pycom.config.Config):
        self.config = config
        self.cursor_window = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self.screen: Optional['curses._CursesWindow'] = curses.initscr()
        self.windows: Dict[str, TermWindow] = {}
        self.logger.info('Curses version: %d.%d.%d', *curses.ncurses_version)
        self.logger.debug('TERM: %s', os.environ['TERM'])

        curses.noecho()
        curses.cbreak()
        self.screen.keypad(True)

        if self.config.colors:
            curses.start_color()
            curses.use_default_colors()
            for i in range(0, curses.COLORS):
                curses.init_pair(i + 1, i, -1)

    def __del__(self):
        self.terminate()

    def clear(self) -> None:
        '''Clear all the windows in the interface'''
        for window in self.windows.values():
            window.clear()

    def getmaxyx(self) -> Tuple[int, int]:
        '''Get the interface maximum dimensions'''
        if self.screen is None:
            return (0, 0)
        return self.screen.getmaxyx()

    def redraw(self) -> None:
        '''Redraw all the windows in the interface'''
        for window in self.windows.values():
            window.redraw()

    def terminate(self) -> None:
        '''Terminates the interface, resetting the user terminal to its usual
        configuration
        '''
        if self.screen is not None:
            self.screen.keypad(False)
        curses.echo()
        curses.nocbreak()
        curses.endwin()
        self.screen = None

    def window_add(self, name: str, title: Optional[str] = None,
                   prompt: bool = False,
                   cursor: bool = False,
                   **kwargs) -> TermWindow:
        '''Add a window in the interface, with a "name", an optional "title",
        and indicate if that window should have a prompt and its cursor
        enabled. Note that curses allows only one cursor (simulating multiple
        is not implemented)
        '''
        self.windows[name] = TermWindow(name, **kwargs)
        if prompt:
            self.windows[name].prompt_enable()
        if title is not None:
            self.windows[name].title_set(title)
        self.windows[name].cursor_enable(cursor)
        self.logger.debug('Adding window %s (%d)', name, cursor)
        return self.windows[name]

    def write(self, window_name: str, lines: Union[str, List[str]]) -> bool:
        '''Write the given "lines" in the window named "window_name", and
        indicates if the window was found'''
        try:
            window = self.windows[window_name]
        except KeyError:
            self.logger.warning('Window %s does not exist', window_name)
            return False
        window.write(lines)
        return True
