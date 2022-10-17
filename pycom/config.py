'''Configuration helper class implementation for PyCom'''

import collections
from copy import deepcopy
import io
import json
import logging.config as logging_config
import tempfile
from typing import Any, Dict, NamedTuple

import serial  # type: ignore

from pycom.utils import (
    OptionalFileOrFilename, dict_update_deep, eval_math_simple,
    project_load_json
)


__author__ = 'Jimmy Durand Wesolowski'
__copyright__ = 'Copyright (C) 2022 Jimmy Durand Wesolowski'
__license__ = 'GPL v2.0'
__version__ = '1.0'


_PARITY_MAP: Dict[str, str] = {
    'none': serial.PARITY_NONE,
    'even': serial.PARITY_EVEN,
    'odd': serial.PARITY_ODD,
    'mark': serial.PARITY_MARK,
    'space': serial.PARITY_SPACE
}


class Config:
    '''Helper class to manage a base default configuration, overridden by a
    JSON file configuration if available, which can be overridden by keyword
    arguments
    '''
    __slots__ = ['_config', 'colors', 'history_save', 'interface',
                 'logging', 'project', 'serial']
    DEFAULT = {
        'colors': True,
        'history_save': True,
        'project': 'DEFAULT',
        'logging': {
            'version': 1,
            'formatters': {
                'full': {
                    'format': (
                        '%(asctime)s %(name)s [%(levelname)s]: %(message)s')
                }
            },
            'handlers': {
                'file': {
                    'backupCount': 1,
                    'class': 'logging.handlers.RotatingFileHandler',
                    'filename': 'logfile.txt',
                    'formatter': 'full',
                    'level': 'DEBUG',
                    'maxBytes': 1024 * 1024,
                    'mode': 'a'
                }
            },
            'loggers': {
                '': {
                    'handlers': ['file'],
                    'level': 'NOTSET'
                }
            }
        },
        'interface': [
            {
                'cols': '{cols}',
                'cursor': False,
                'lines': 3,
                'name': 'error',
                'posy': '{lines} - 3',
                'posx': 0,
                'title': 'Information'
            },
            {
                'cols': '{cols} // 2',
                'cursor': False,
                'lines': '{lines} - 3',
                'name': 'serial',
                'posy': 0,
                'posx': '{cols} // 2',
                'title': 'Serial'
            },
            {
                'cols': '{cols} // 2',
                'cursor': True,
                'lines': '{lines} - 3',
                'name': 'command',
                'posy': 0,
                'posx': 0,
                'prompt': True,
                'title': 'Commands'
            }
        ],
        'serial': {
            'baudrate': 115200,
            'bytesize': 8,
            'port': '/dev/ttyUSB0',
            'parity': _PARITY_MAP['none'],
            'stopbits': 1
        }
    }
    DEFAULT_CONFIG = 'config.json'

    class SerialConfig(collections.namedtuple(
            'SerialConfig',
            ['baudrate', 'bytesize', 'parity', 'port', 'stopbits'])):
        '''Namedtuple for serial port configuration'''
        def __new__(cls, **params):
            parity = params.pop('parity')
            try:
                parity = _PARITY_MAP[parity]
            except KeyError:
                pass
            return super().__new__(cls, **params, parity=parity)

    def __init__(self, config_fd: OptionalFileOrFilename = None,
                 **kwargs):
        self.colors: bool
        self.history_save: bool
        self.interface: Dict[str, Any] = {}
        self.logging: Dict[str, Any] = {}
        self.project: str
        self.serial: NamedTuple

        self._config: Dict[str, Any] = deepcopy(self.DEFAULT)
        self.load_file(config_fd)
        self.load_dict(kwargs)
        for key in ['colors', 'history_save', 'project', 'logging',
                    'interface']:
            setattr(self, key, self._config[key])
        self.serial = Config.SerialConfig(**self._config['serial'])
        logging_config.dictConfig(self.logging)

    def load_dict(self, values: Dict[str, Any]) -> None:
        '''Load the given dictionary "values" to override the configuration
        '''
        try:
            log_values: Dict[str, Any] = values.pop('logging')
            log_current: Dict[str, Any] = self._config['logging']
            self._config['logging'] = dict_update_deep(log_current, log_values)
        except KeyError:
            pass
        for key in Config.SerialConfig._fields:
            try:
                self._config['serial'][key] = values.pop(key)
            except KeyError:
                pass
        for key, value in values.items():
            self._config[key] = value

    def load_file(self, config_fd: OptionalFileOrFilename = None):
        '''Load the given JSON filename or file descriptor "config_fg" to
        override the configuration
        '''
        # pylint: disable=protected-access # type hin
        if isinstance(config_fd,
                      (io.TextIOBase, tempfile._TemporaryFileWrapper)):
            config = json.load(config_fd)
        else:
            filename: str = self.DEFAULT_CONFIG
            if config_fd is not None:
                if not isinstance(config_fd, str):
                    raise TypeError
                filename = config_fd
            config = project_load_json(filename, toolname=None, default={})
        self.load_dict(config)

    def interface_parse(self, **format_dict):
        '''Interpret the interface values if they contain simple math
        operations on "cols", "lines", "posx", and "posy", respectively the
        interface window column number, line number, and its x and y position
        in the interface. The values should be passed as keywords in
        "format_dict" as needed
        '''
        for params in self.interface:
            for key in ['cols', 'lines', 'posx', 'posy']:
                try:
                    formatted = params[key].format(**format_dict)
                    params[key] = eval_math_simple(formatted)
                except AttributeError:
                    pass
