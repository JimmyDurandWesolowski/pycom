'''Main class that handles the terminal'''

import logging
import os
import queue
import select
import sys
import threading
import traceback
from typing import Dict, List, Optional, Union

import serial  # type: ignore

import pycom.command
import pycom.completion
import pycom.config
import pycom.cursorpos
import pycom.history
from pycom.mode import Mode
import pycom.terminal
import pycom.term_win
import pycom.utils
from pycom.utils import FileType

__author__ = 'Jimmy Durand Wesolowski'
__copyright__ = 'Copyright (C) 2022 Jimmy Durand Wesolowski'
__license__ = 'GPL v2.0'
__version__ = '1.0'


NAME = 'pycom'


TITLE_MODE = {
    Mode.COMPLETION: 'Completion mode',
    Mode.ESCAPE: '(escaped mode) commands',
    Mode.HISTORY: 'History mode',
    Mode.NORMAL: 'Commands',
    Mode.SEARCH: 'Search mode',
}


class TerminalSerial(threading.Thread):
    '''Thread class handling the serial communication retrieval and
    forwarding
    '''
    def __init__(self, interface, config, condition):
        super().__init__()
        self.config = config
        self.condition = condition
        self.interface = interface
        self.logger = logging.getLogger(self.__class__.__name__)
        self.queue: queue.Queue = queue.Queue()

    @staticmethod
    def _serial_get(serial_port) -> None:
        try:
            data = serial_port.read_until()
        except serial.SerialException:
            return None
        if not data:
            return None
        return data.decode('ascii', 'ignore')

    def _queue_get(self, serial_port) -> None:
        try:
            data = self.queue.get_nowait()
        except queue.Empty:
            return
        try:
            self.logger.info('Sending "%s" on serial', data)
            serial_port.write((str(data) + os.linesep).encode('ascii'))
        except serial.SerialException as exc:
            self.logger.warning('error writing serial: %s', exc)

    def run(self) -> None:
        self.logger.debug('Starting serial')
        window = self.interface.windows['serial']
        serial_port = serial.Serial(self.config.serial.port,
                                    self.config.serial.baudrate,
                                    timeout=.1)
        lines: List[pycom.term_win.TermLine] = []
        while not self.condition.is_set():
            self._queue_get(serial_port)
            data = self._serial_get(serial_port)
            if data is None:
                continue
            if not lines:
                lines.append(window.line_create(data.rstrip()))
            else:
                lines[-1] += data.rstrip()
            if data[-1] == '\n':
                lines.append(window.line_create())
            self.logger.info('%d lines', len(lines))
            window.write(lines)
            self.interface.redraw()

    def write(self, content: Union[bytes, bytearray, List[str], str]) -> None:
        '''Write to the serial port and serial terminal'''
        if isinstance(content, list):
            content = os.linesep.join(content)
        if isinstance(content, (bytearray, bytes)):
            content = content.decode('utf-8', 'ignore')
        self.queue.put(content)


class TerminalOperation(pycom.terminal.Terminal):
    '''Terminal handling the command editing'''
    def __init__(self, interface: pycom.term_win.Interface,
                 window: pycom.term_win.TermWindow,
                 serial_port,
                 config: pycom.config.Config,
                 condition: threading.Event):
        self.cmd_table: Dict[Mode, pycom.command.Command]
        self.condition: threading.Event = condition
        self.config = config
        self.completion: pycom.completion.Completion
        self.history = pycom.history.History()
        self.interface = interface
        self.line_current: pycom.term_win.TermLine
        self.lines: List[pycom.term_win.TermLine] = []
        self.logger: logging.Logger = logging.getLogger(
            self.__class__.__name__)
        self.mode: Mode = Mode.NORMAL
        self.serial = serial_port
        self.window: pycom.term_win.TermWindow = window

        self.cmd_table = {
            Mode.COMPLETION: pycom.command.Command(self),
            Mode.ESCAPE: pycom.command.Command(self),
            Mode.HISTORY: pycom.command.CommandHistory(self),
            Mode.NORMAL: pycom.command.Command(self),
            # FIXME: to be implemented
            # Mode.SEARCH: pycom.command.CommandSearch(self),
            Mode.SEARCH: pycom.command.Command(self),
        }

        completion_config = pycom.utils.project_load_json(
            'completion.json', NAME, default={})
        proj = config.project
        self.logger.debug('Loading completion for "%s"', proj)
        try:
            completion_config = completion_config[proj]
        except KeyError:
            msg = f'Completion for "{proj}" not found, completion disabled'
            self.logger.warning(msg)
            self.interface.write('error', msg)
        self.completion = pycom.completion.Completion(completion_config)
        try:
            self.history.load(config.history_save)
        except pycom.history.History.Error as exc:
            msg = f'Failed to load history: "{exc}"'
            self.logger.warning(msg)
            self.interface.write('error', msg)

        self.mode_set(Mode.NORMAL)
        self.line_current = self.window.line_create(num=len(self.lines) + 1)

    def clear(self):
        self.window.write()

    def mode_set(self, mode: Mode) -> None:
        if mode == self.mode:
            return
        if mode == Mode.HISTORY and not self.history:
            self.interface.write('error', 'No command in history')
            return
        self.logger.info('Mode switch %s -> %s', self.mode, mode)
        self.window.clear()
        self.mode = mode
        self.cmd_table[mode].start()
        self.window.title_set(TITLE_MODE[mode])

    def newline(self) -> None:
        self.logger.debug('MODE: %s', self.mode)
        if self.mode == Mode.HISTORY:
            self.line_current = self.window.line_create(
                self.history[self.history.pos], num=len(self.lines) + 1)
        self.logger.info('Current line: %s', self.line_current)
        self.lines.append(self.line_current)
        self.serial.write(self.line_current)
        try:
            self.history.append(str(self.line_current))
        except pycom.history.History.Error as exc:
            msg = f'Failed to add to history: "{exc}"'
            self.logger.warning(msg)
            self.interface.write('error', msg)
        self.line_current = self.window.line_create(num=len(self.lines) + 1)

    def overwrite(self, content):
        self.line_current = self.window.line_create(
            str(content), num=len(self.lines) + 1)

    def pos_update(self, pos: pycom.cursorpos.CursorPos) -> None:
        if self.line_current is None:
            raise AssertionError
        self.line_current.update_pos(pos)

    def read(self) -> None:
        try:
            key = self.window.read()
        except KeyboardInterrupt:
            self.terminate()
            return
        self.logger.debug('Key read: %d', key)
        self.cmd_table[self.mode](key)

    def reset(self):
        raise NotImplementedError

    def terminate(self) -> None:
        self.condition.set()

    def update(self):
        self.window.cursor_enable(True)
        if self.mode == Mode.HISTORY:
            self.window.cursor_enable(False)
            lines = []
            for idx, line in enumerate(self.history):
                line = self.window.line_create(str(line), num=idx + 1)
                if idx == self.history.pos:
                    line.highlight()
                lines.append(line)
            self.window.write(lines)
            return
        if self.mode == Mode.SEARCH:
            self.window.cursor_enable(False)
            lines = []
            for idx, line in enumerate(self.history.search(self.line_current)):
                line = self.window.line_create(str(line), num=idx + 1)
                if idx == self.history.pos:
                    line.highlight()
                lines.append(line)
            self.window.write(lines)
            return
        self.window.write(self.lines + [self.line_current])

    def write(self, lines: List[str]):
        start = len(self.lines)
        curline = None
        if lines[-1][-1] != os.linesep:
            curline = lines[-1]
            lines = lines[:-1]
        for idx, line in enumerate(lines):
            self.lines.append(
                self.window.line_create(line, num=start + idx + 1))
        if curline is None:
            return
        self.line_current = self.window.line_create(
            curline, num=len(self.lines) + 1)


class PyCom:
    '''Terminal threads and interface handling'''
    def __init__(self, config=None):
        self.config = config
        self.input_content: List[str] = []
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info('Starting session')
        self.logger.info('_' * 60)

    def _run(self) -> None:
        event = threading.Event()
        event.clear()
        interface = pycom.term_win.Interface(self.config)
        lines, cols = interface.getmaxyx()
        self.logger.debug('Interface size: %dx%d', lines, cols)
        self.config.interface_parse(lines=lines, cols=cols)
        for params in self.config.interface:
            interface.window_add(**params)
        serial_port = TerminalSerial(interface, self.config, event)
        opterm = TerminalOperation(interface, interface.windows['command'],
                                   serial_port, self.config, event)
        if self.input_content:
            self.logger.info('Received input content: %s', self.input_content)
            opterm.write(self.input_content)

        interface.clear()
        serial_port.start()
        while not event.is_set():
            opterm.update()
            self.logger.debug('Queue %d',
                              interface.windows['command'].queue.qsize())
            interface.redraw()
            if interface.windows['error'].queue.qsize():
                interface.windows['error'].clear()
            opterm.read()
        interface.terminate()

    def input_load(self, input_files: Optional[List[FileType]]) -> bool:
        '''Load the lines from the given files if any and stdin to pass to the
        command terminal
        '''
        self.input_content = []
        if input_files is not None:
            for filename in input_files:
                with open(filename, encoding='ascii') as input_fd:
                    self.input_content += input_fd.readlines()

        if select.select([sys.stdin, ], [], [], 0.0)[0]:
            self.input_content += sys.stdin.readlines()
            with open("/dev/tty", encoding='ascii') as ttyfd:
                os.dup2(ttyfd.fileno(), 0)
            return True
        self.logger.info('No input from stdin')
        return False

    def run(self) -> None:
        '''Run PyCom'''
        try:
            self._run()
        except Exception as exc:
            self.logger.critical('Exception caught:%s%s', os.linesep,
                                 traceback.format_exc())
            raise exc
