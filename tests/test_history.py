import os
import tempfile
import unittest
import unittest.mock

from tests.common import TestCommon
from pycom.config import Config
import pycom.history
from pycom.history import History


class TestHistory(TestCommon):
    def setUp(self):
        super().setUp()
        self.history = History()

    def test_init_no_load(self):
        self.assertEqual(self.history.pos, -1)
        self.assertEqual(list(self.history), [])
        self.history.append('test')
        self.assertEqual(len(self.history), 1)
        self.assertEqual(self.history.pos, 0)
        self.assertEqual(list(self.history), ['test'])

    def test_init_no_config(self):
        temp_name = next(tempfile._get_candidate_names())
        with self.assertRaises(History.Error):
            self.history.load(True, temp_name)
        self.assertEqual(self.history.pos, -1)
        self.assertEqual(list(self.history), [])
        self.assertEqual(self.history.line_current, None)

    def test_init_empty_config(self):
        with tempfile.NamedTemporaryFile() as temp_name:
            self.history.load(True, temp_name.name)
        self.assertEqual(self.history.pos, -1)
        self.assertEqual(list(self.history), [])

    def test_init_default_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            with unittest.mock.patch.dict(os.environ, {'HOME':  tmp}):
                with self.assertRaises(History.Error):
                    self.history.load()
                self.history.load(False)

    def test_append_empty_line(self):
        self.assertEqual(self.history.pos, -1)
        self.assertEqual(list(self.history), [])
        self.history.append('')
        self.assertEqual(self.history.pos, -1)
        self.assertEqual(len(self.history), 0)
        self.assertEqual(list(self.history), [])

    def test_append_twice(self):
        self.assertEqual(self.history.pos, -1)
        self.assertEqual(list(self.history), [])
        self.history.append('test1')
        self.assertEqual(list(self.history), ['test1'])
        self.assertEqual(self.history.pos, 0)
        self.assertEqual(len(self.history), 1)
        self.assertEqual(self.history.line_current, 'test1')
        self.history.append('test1')
        self.assertEqual(len(self.history), 1)
        self.assertEqual(list(self.history), ['test1'])
        self.assertEqual(self.history.pos, 0)
        self.assertEqual(self.history.line_current, 'test1')
        self.history.append('test2')
        self.assertEqual(self.history.pos, 1)
        self.assertEqual(len(self.history), 2)
        self.assertEqual(list(self.history), ['test1', 'test2'])
        self.assertEqual(self.history.line_current, 'test2')
        self.history.append('test1')
        self.assertEqual(len(self.history), 2)
        self.assertEqual(list(self.history), ['test2', 'test1'])
        self.assertEqual(self.history.pos, 1)
        self.assertEqual(self.history.line_current, 'test1')
        self.history.append('test1')
        self.assertEqual(self.history.pos, 1)
        self.assertEqual(len(self.history), 2)
        self.assertEqual(list(self.history), ['test2', 'test1'])
        self.assertEqual(self.history.line_current, 'test1')
        self.history.append('test2')
        self.assertEqual(self.history.pos, 1)
        self.assertEqual(len(self.history), 2)
        self.assertEqual(list(self.history), ['test1', 'test2'])
        self.assertEqual(self.history.line_current, 'test2')
        self.history.append('test3')
        self.assertEqual(self.history.pos, 2)
        self.assertEqual(len(self.history), 3)
        self.assertEqual(list(self.history), ['test1', 'test2', 'test3'])
        self.assertEqual(self.history.line_current, 'test3')
        self.history.append('test1')
        self.assertEqual(self.history.pos, 2)
        self.assertEqual(len(self.history), 3)
        self.assertEqual(list(self.history), ['test2', 'test3', 'test1'])
        self.assertEqual(self.history.line_current, 'test1')

    def test_load(self):
        data = ['line1', 'line2', 'line3']
        with tempfile.NamedTemporaryFile('w+t') as temp_name:
            temp_name.write(os.linesep.join(data))
            temp_name.seek(0)
            self.history.load(True, temp_name.name)
        self.assertEqual(self.history.pos, 2)
        self.assertEqual(list(self.history), data)

        with tempfile.TemporaryDirectory() as tmp:
            with unittest.mock.patch.dict(os.environ, {'HOME':  tmp}):
                with open(os.path.join(tmp, '.pycom_history'), 'w+') as hfd:
                    hfd.write(os.linesep.join(data))
                self.history.load()
                self.assertEqual(self.history.pos, 5)
                self.assertEqual(list(self.history), data + data)
                self.history.save()
                with open(os.path.join(tmp, '.pycom_history')) as hfd:
                    content = hfd.read()
        self.assertEqual(os.linesep.join(data + data) + os.linesep, content)

        with tempfile.TemporaryDirectory() as tmp:
            with unittest.mock.patch.dict(os.environ, {'HOME':  tmp}):
                with self.assertRaises(pycom.history.History.Error):
                    self.history.save()

    def test_pos_update_empty(self):
        self.assertEqual(list(self.history), [])
        self.assertEqual(len(self.history), 0)
        self.assertEqual(self.history.pos, -1)
        self.assertTrue(self.history.pos_update(-1))
        self.assertEqual(self.history.pos, 0)
        self.assertFalse(self.history.pos_update(1))
        self.assertEqual(self.history.pos, 0)

    def test_pos_update(self):
        data = ['line1', 'line2', 'line3']
        with tempfile.NamedTemporaryFile('w+t') as temp_name:
            temp_name.write(os.linesep.join(data))
            temp_name.seek(0)
            self.history.load(True, temp_name.name)
        self.assertEqual(self.history.pos, 2)
        self.assertEqual(list(self.history), data)
        self.assertTrue(self.history.pos_update(-1))
        self.assertEqual(self.history.pos, 1)
        self.assertTrue(self.history.pos_update(1))
        self.assertEqual(self.history.pos, 2)
        self.assertFalse(self.history.pos_update(1))
        self.assertEqual(self.history.pos, 2)
        self.assertTrue(self.history.pos_update(-1))
        self.assertEqual(self.history.pos, 1)
        self.assertTrue(self.history.pos_update(-1))
        self.assertEqual(self.history.pos, 0)
        self.assertTrue(self.history.pos_update(-1))
        self.assertEqual(self.history.pos, 0)
