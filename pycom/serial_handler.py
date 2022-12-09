'''Serial communication handling class implementation'''

import datetime
import logging
import os
import queue
import threading
import time
from typing import List, Union

import serial  # type: ignore

import pycom.term_win

__author__ = 'Jimmy Durand Wesolowski'
__copyright__ = 'Copyright (C) 2022 Jimmy Durand Wesolowski'
__license__ = 'GPL v2.0'
__version__ = '1.0'


class SerialHandler(threading.Thread):
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
        self.ratelimit: datetime.datetime.timedelta
        self.ratelimit = self.config.serial.ratelimit
        self.serial_port = None

    def _serial_write(self, data: str):
        content = data.encode('ascii')
        if not self.config.serial.ratelimit:
            self.serial_port.write(content)
            return
        for char in content:
            end = datetime.datetime.utcnow() + self.ratelimit
            self.serial_port.write(char)
            delay = (end - datetime.datetime.utcnow()).total_seconds()
            self.logger.warning('Delay: %f %s', delay, self.ratelimit)
            if delay > 0:
                time.sleep(delay)

    def _serial_get(self) -> Union[None, str]:
        try:
            data = self.serial_port.read_until()
        except serial.SerialException:
            return None
        if not data:
            return None
        return data.decode('ascii', 'ignore')

    def _queue_get(self) -> None:
        try:
            data = self.queue.get_nowait()
        except queue.Empty:
            return
        self.logger.info('Sending "%s" on serial', data)
        try:
            self._serial_write(str(data) + os.linesep)
        except (TypeError, ValueError, serial.SerialException) as exc:
            self.logger.warning('error writing serial: %s', exc)

    def run(self) -> None:
        self.logger.debug('Starting serial')
        window = self.interface.windows['serial']
        self.serial_port = serial.Serial(self.config.serial.port,
                                         self.config.serial.baudrate,
                                         timeout=.1)
        lines: List[pycom.term_win.TermLine] = []
        while not self.condition.is_set():
            self._queue_get()
            data = self._serial_get()
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
