from copy import deepcopy
import json
import logging
import logging.config
import os
from pathlib import Path
import tempfile
import unittest.mock

from tests.common import TestCommon
from pycom.config import Config
from pycom.utils import eval_math_simple, project_load_json


class TestConfig(TestCommon):
    def _conf_file(self, **kwargs):
        self.def_config = tempfile.NamedTemporaryFile(mode='a+t')
        json.dump(kwargs, self.def_config)
        self.def_config.seek(0)
        Config.DEFAULT_CONFIG = self.def_config.name

    def setUp(self):
        super().setUp()
        self.default = deepcopy(Config.DEFAULT)

    def tearDown(self):
        self.assertEqual(Config.DEFAULT, self.default)
        super().tearDown()

    @unittest.mock.patch(
        'logging.config.dictConfig',
        unittest.mock.Mock(side_effect=logging.config.dictConfig))
    def test_default(self):
        self._conf_file()
        config = Config()
        self.assertEqual(config.colors, Config.DEFAULT['colors'])
        self.assertEqual(config.logging, Config.DEFAULT['logging'])
        self.assertEqual(config.serial, Config.SerialConfig(
            **Config.DEFAULT['serial']))
        logging.config.dictConfig.assert_called_once_with(config.logging)

    def test_no_config(self):
        Config.DEFAULT_CONFIG_PATH = 'invalid config file'
        config = Config()
        self.assertEqual(config.colors, Config.DEFAULT['colors'])
        self.assertEqual(config.logging, Config.DEFAULT['logging'])
        self.assertEqual(config.serial, Config.SerialConfig(
            **Config.DEFAULT['serial']))

    def test_config_bad_type(self):
        with self.assertRaises(TypeError):
            config = Config(1)

    def test_config_file(self):
        def_config = tempfile.NamedTemporaryFile(mode='a+t')
        json.dump({'history_save': False, 'colors': False}, def_config)
        def_config.seek(0)
        config = Config(def_config)
        self.assertFalse(config.colors)
        self.assertFalse(config.history_save)
        self.assertEqual(config.logging, Config.DEFAULT['logging'])
        self.assertEqual(config.serial, Config.SerialConfig(
            **Config.DEFAULT['serial']))

    def test_config_filename(self):
        def_config = tempfile.NamedTemporaryFile(mode='a+t')
        json.dump({'history_save': False, 'colors': False}, def_config)
        def_config.seek(0)
        config = Config(def_config.name)
        self.assertFalse(config.colors)
        self.assertFalse(config.history_save)
        self.assertEqual(config.serial, Config.SerialConfig(
            **Config.DEFAULT['serial']))

    def test_overwrite_conf_file(self):
        self._conf_file(history_save=False, colors=False)
        config = Config()
        self.assertFalse(config.colors)
        self.assertFalse(config.history_save)
        self.assertEqual(config.logging, Config.DEFAULT['logging'])
        self.assertEqual(config.serial, Config.SerialConfig(
            **Config.DEFAULT['serial']))

    def test_overwrite_args(self):
        self._conf_file()
        config = Config(port='/dev/ttyS0', history_save=False)
        self.assertEqual(config.colors, Config.DEFAULT['colors'])
        self.assertFalse(config.history_save)
        self.assertEqual(config.logging, Config.DEFAULT['logging'])
        self.assertEqual(config.serial.baudrate,
                         Config.DEFAULT['serial']['baudrate'])
        self.assertEqual(config.serial.bytesize,
                         Config.DEFAULT['serial']['bytesize'])
        self.assertEqual(config.serial.parity,
                         Config.DEFAULT['serial']['parity'])
        self.assertEqual(config.serial.stopbits,
                         Config.DEFAULT['serial']['stopbits'])
        self.assertEqual(config.serial.port, '/dev/ttyS0')

    def test_overwrite_config_args(self):
        self._conf_file(colors=False)
        config = Config(port='/dev/ttyS0', history_save=False)
        self.assertFalse(config.colors)
        self.assertFalse(config.history_save)
        self.assertEqual(config.logging, Config.DEFAULT['logging'])
        self.assertEqual(config.serial.baudrate,
                         Config.DEFAULT['serial']['baudrate'])
        self.assertEqual(config.serial.bytesize,
                         Config.DEFAULT['serial']['bytesize'])
        self.assertEqual(config.serial.parity,
                         Config.DEFAULT['serial']['parity'])
        self.assertEqual(config.serial.stopbits,
                         Config.DEFAULT['serial']['stopbits'])
        self.assertEqual(config.serial.port, '/dev/ttyS0')

    def test_overwrite_config_args_logging(self):
        log_conf_up = {
            'formatters': {
                'simple': {
                    'format': '%(message)s'
                }
            }
        }
        self._conf_file(history_save=False, logging=log_conf_up)
        config = Config(port='/dev/ttyS0', history_save=False)
        self.assertEqual(config.colors, Config.DEFAULT['colors'])
        self.assertFalse(config.history_save)
        self.assertEqual(config.logging['formatters']['simple'],
                         log_conf_up['formatters']['simple'])
        self.assertEqual(config.logging['formatters']['full'],
                         Config.DEFAULT['logging']['formatters']['full'])
        self.assertEqual(config.serial.baudrate,
                         Config.DEFAULT['serial']['baudrate'])
        self.assertEqual(config.serial.bytesize,
                         Config.DEFAULT['serial']['bytesize'])
        self.assertEqual(config.serial.parity,
                         Config.DEFAULT['serial']['parity'])
        self.assertEqual(config.serial.stopbits,
                         Config.DEFAULT['serial']['stopbits'])
        self.assertEqual(config.serial.port, '/dev/ttyS0')

    def test_bad_logconfig_assert(self):
        log_conf_up = {
            'formatters': {
                'simple': '%(message)s'
            }
        }
        with self.assertRaises(ValueError):
            config = Config(logging=log_conf_up)

    def test_interface(self):
        data = {
            'interface': [
                {
                    'lines': 3,
                    'cols': '{cols}',
                    'name': 'error',
                    'posy': '{lines} - 3',
                    'posx': 0,
                    'title': 'Information'
                },
                {
                    'cols': '{cols} // 2',
                    'lines': '{lines} - 3',
                    'name': 'serial',
                    'posy': 0,
                    'posx': '{cols} // 2',
                    'title': 'Serial'
                },
                {
                    'cols': '{cols} // 2',
                    'lines': '{lines} - 3',
                    'name': 'command',
                    'posy': 0,
                    'posx': 0,
                    'prompt': True,
                    'title': 'Commands'
                }
            ]
        }
        interface_parsed = [
            {
                'cols': 40,
                'lines': 3,
                'name': 'error',
                'posy': 27,
                'posx': 0,
                'title': 'Information'
            },
            {
                'cols': 20,
                'lines': 27,
                'name': 'serial',
                'posy': 0,
                'posx': 20,
                'title': 'Serial'
            },
            {
                'cols': 20,
                'lines': 27,
                'name': 'command',
                'posy': 0,
                'posx': 0,
                'prompt': True,
                'title': 'Commands'
            }
        ]
        self._conf_file(**data)
        config = Config()
        config.interface_parse(cols=40, lines=30)
        self.assertEqual(config.interface, interface_parsed)
