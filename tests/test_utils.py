import json
import logging
import logging.config
import os
from pathlib import Path
import tempfile
import unittest.mock

from tests.common import TestCommon
from pycom.utils import (
    chunks, dict_update_deep, eval_math_simple, logging_level, project_load_json
)


class TestDictUpdate(TestCommon):
    def test_add(self):
        self.assertEqual(dict_update_deep({'a': 1}, {'b': 2}),
                         {'a': 1, 'b': 2})

    def test_merge(self):
        self.assertEqual(
            dict_update_deep({'a': 1, 'b': 2}, {'b': 'two', 'c': 'three'}),
            {'a': 1, 'b': 'two', 'c': 'three'})

    def test_merge_deep(self):
        dict1 = {
            'a': 1,
            'b': {
                'value': 2,
                'subelement': {
                    'c': 3
                }
            }
        }
        dict2 = {
            'b': {
                'value': 'two'
            }
        }
        exp = {
            'a': 1,
            'b': {
                'value': 'two',
                'subelement': {
                    'c': 3
                }
            }
        }
        self.assertEqual(dict_update_deep(dict1, dict2), exp)

    def test_merge_deeper(self):
        dict1 = {
            'a': 1,
            'b': {
                'value': 2,
                'subelement': {
                    'c': {
                        'value': 3,
                        'subelement': {
                            'd': {
                                'value': 4
                            }
                        }
                    }
                }
            }
        }
        dict2 = {
            'b': {
                'value': 'two',
                'subelement': {
                    'c': {
                        'subelement': {
                            'e': 5
                        }
                    }
                }
            }
        }
        exp = {
            'a': 1,
            'b': {
                'value': 'two',
                'subelement': {
                    'c': {
                        'value': 3,
                        'subelement': {
                            'd': {
                                'value': 4
                            },
                            'e': 5
                        }
                    }
                }
            }
        }
        self.assertEqual(dict_update_deep(dict1, dict2), exp)



class TestProjectLoadJson(TestCommon):
    def test_filename(self):
        data = {'a': 1, 'b': 2, 'c': 3}
        temp = tempfile.NamedTemporaryFile(mode='a+t')
        json.dump(data, temp)
        temp.seek(0)
        self.assertEqual(data, project_load_json(temp.name))
        path = Path(temp.name)
        os.chdir(path.parent)
        self.assertEqual(data, project_load_json(path.name))

    def test_config_default(self):
        data = {'a': 1, 'b': 2, 'c': 3}
        toolname = 'toolname'
        with tempfile.TemporaryDirectory() as tmp:
            with unittest.mock.patch.dict(os.environ, {'HOME':  tmp}):
                config_dir = os.path.join(tmp, '.config', toolname)
                config_file = 'dummy_config.json'
                os.makedirs(config_dir)
                config_path = os.path.join(config_dir, config_file)
                with open(config_path, 'w+t') as config_fd:
                    json.dump(data, config_fd)
                self.assertEqual(data, project_load_json(filename=config_file,
                                                         toolname=toolname))


class MockLogging(unittest.mock.MagicMock):
    LOGGERS = {}
    NOTSET, DEBUG, INFO, WARN, WARNING, ERROR, CRITICAL = 0, 1, 2, 3, 3, 4, 5

    def getLogger(name=None):
        MockLogging.LOGGERS[name] = unittest.mock.MagicMock()
        MockLogging.LOGGERS[name].level = MockLogging.NOTSET
        return MockLogging.LOGGERS[name]


class TestLoggingInit(TestCommon):
    @unittest.mock.patch('pycom.utils.logging', new_callable=MockLogging)
    def test_none(self, logging_mocked):
        logging_level()
        logging_mocked.getLogger().level = logging_mocked.WARNING

    @unittest.mock.patch('pycom.utils.logging', new_callable=MockLogging)
    def test_zer0(self, logging_mocked):
        logging_level(0)
        logging_mocked.getLogger().level = logging_mocked.WARNING

    @unittest.mock.patch('pycom.utils.logging', new_callable=MockLogging)
    def test_info(self, logging_mocked):
        logging_level(1)
        logging_mocked.getLogger().level = logging_mocked.INFO

    @unittest.mock.patch('pycom.utils.logging', new_callable=MockLogging)
    def test_debug(self, logging_mocked):
        logging_level(2)
        logging_mocked.getLogger().level = logging_mocked.DEBUG

    @unittest.mock.patch('pycom.utils.logging', new_callable=MockLogging)
    def test_debug_higher(self, logging_mocked):
        logging_level(3)
        logging_mocked.getLogger().level = logging_mocked.DEBUG


class TestChunk(TestCommon):
    def test_empty(self):
        self.assertEqual(list(chunks([], 1)), [])
        self.assertEqual(list(chunks([], 2)), [])
        self.assertEqual(list(chunks([], 10)), [])

    def test_one(self):
        self.assertEqual(list(chunks([1], 1)), [[1]])
        self.assertEqual(list(chunks([1], 2)), [[1]])
        self.assertEqual(list(chunks([1], 10)), [[1]])

    def test_one_chunk(self):
        self.assertEqual(list(chunks([1, 2, 3], 1)), [[1], [2], [3]])
        self.assertEqual(list(chunks([1], 2)), [[1]])
        self.assertEqual(list(chunks([1], 10)), [[1]])

    def test_chunks(self):
        self.assertEqual(list(chunks([1, 2, 3], 2)), [[1, 2], [3]])


class TestEvalMathSimple(TestCommon):
    def test_num(self):
        self.assertEqual(eval_math_simple(2), 2)
        self.assertEqual(eval_math_simple(42), 42)

    def test_num_str(self):
        self.assertEqual(eval_math_simple('2'), 2)
        self.assertEqual(eval_math_simple('42'), 42)

    def test_add_2(self):
        self.assertEqual(eval_math_simple('2 + 1'), 3)
        self.assertEqual(eval_math_simple('2+ 3'), 5)
        self.assertEqual(eval_math_simple('2 +9'), 11)
        self.assertEqual(eval_math_simple('2+4'), 6)

    def test_add_3(self):
        self.assertEqual(eval_math_simple('2 + 1+5'), 8)

    def test_add_mul(self):
        self.assertEqual(eval_math_simple('2 + 5* 3'), 17)

    def test_add_mul_long(self):
        self.assertEqual(eval_math_simple('3 + 14*2 + 10*2'),
                                          3 + 14 * 2 + 10 * 2)
        self.assertEqual(eval_math_simple('2 + 5* 3 + 14*2 + 10*2'),
                         2 + 5 * 3 + 14 * 2 + 10 * 2)

    def test_add_mul_div(self):
        self.assertEqual(eval_math_simple('2 + 5* 3 + 14/2 + 10/2'),
                         2 + 5 * 3 + 14 / 2 + 10 / 2)

    def test_add_mul_div2(self):
        self.assertEqual(eval_math_simple('2 + 5* 3 + 14/2 + 10//2'),
                         2 + 5 * 3 + 14 / 2 + 10 // 2)

    def test_unknown(self):
        self.assertEqual(eval_math_simple('2 % 5'), None)
