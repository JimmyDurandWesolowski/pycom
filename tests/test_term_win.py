from collections import namedtuple
import logging
import os
import sys
import unittest.mock

from tests.common import TestCommon
from pycom.config import Config
import pycom.term_win
from pycom.term_win import Interface, TermLine, TermWindow
from pycom.cursorpos import CursorPos
from pycom.window import Window


class TestTermLine(TestCommon):
    COL_NB = 30
    LINE_NB = 25

    def setUp(self):
        super().setUp()
        self.line = TermLine(self.LINE_NB, self.COL_NB)

    def test_assert(self):
        with self.assertRaises(AssertionError):
            self.line.pos = -1
            self.line.content

        with self.assertRaises(AssertionError):
            self.line.pos = 1
            self.line.content

        with self.assertRaises(AssertionError):
            test = namedtuple('Test', 'value')('a')
            self.line.update_pos(test)

    def test_line_compare(self):
        self.line = TermLine(self.LINE_NB, self.COL_NB, '123')
        self.assertEqual(hash(self.line), hash(TermLine(1, 2, '123')))
        self.assertEqual(self.line, TermLine(1, 2, '123'))

    def test_line_empty(self):
        self.line = TermLine(self.LINE_NB, self.COL_NB)
        self.assertEqual(str(self.line), '')

    def test_line_content(self):
        line_content = 'small line'
        line = TermLine(self.LINE_NB, self.COL_NB, line_content)
        self.assertEqual(line._content, line_content)
        self.assertEqual(len(line), len(line_content))
        self.assertEqual(line.get(), [line_content])
        self.assertEqual(line.pos, len(line_content))
        self.assertEqual(line.screen_pos, (0, len(line_content)))
        self.assertEqual(str(line), 'small line')

    def test_line_edit(self):
        line_content = 'small line'
        line = TermLine(self.LINE_NB, self.COL_NB, line_content)
        line.update_pos(CursorPos.LEFT)
        self.assertEqual(line.pos, len(line_content) - 1)
        line.update_pos(CursorPos.LEFT)
        self.assertEqual(line.pos, len(line_content) - 2)
        line += 'a'
        self.assertEqual(line.pos, len(line_content) - 1)
        self.assertEqual(line._content, 'small liane')
        line += ' '
        self.assertEqual(line.pos, len(line_content))
        self.assertEqual(line._content, 'small lia ne')

    def test_line_content_long(self):
        part = 'very long line'
        dashes = '-' * self.COL_NB
        line_content = dashes + part + dashes
        line = TermLine(self.LINE_NB, self.COL_NB, line_content)
        self.assertEqual(line._content, line_content)
        self.assertEqual(line.get(), [
            dashes, part + '-' * (self.COL_NB - len(part)), '-' * len(part)])
        self.assertEqual(line.pos, len(line_content))
        self.assertEqual(line.screen_pos, (2, len(part)))

        self.assertEqual(line.get(1), ['-' * len(part)])
        self.assertEqual(line.get(2), [part + '-' * (self.COL_NB - len(part)),
                                       '-' * len(part)])
        dash_str = dashes[len(part) + 3:] + part + dashes + '...'
        self.assertEqual(repr(line), f'[TermLine 3 line(s) "{dash_str}"]')
        self.assertEqual(str(line), line_content)

    def test_line_content_full(self):
        line_content = '-' * self.COL_NB * self.LINE_NB
        part = 'very long line'
        line_content += part
        line = TermLine(self.LINE_NB, self.COL_NB, line_content)
        self.assertEqual(line._content, line_content)
        self.assertEqual(
            line.get(), ['-' * self.COL_NB] * (self.LINE_NB - 1) + [part])

    def test_write_char(self):
        self.line.write('a')
        self.assertEqual(self.line.content, ['a'])
        self.line.write('b')
        self.assertEqual(self.line.content, ['ab'])
        self.assertEqual(self.line.pos, 2)
        self.assertEqual(self.line.screen_pos, (0, 2))

    def test_fullline(self):
        self.line.write('-' * self.COL_NB)
        self.assertEqual(self.line.content, ['-' * self.COL_NB])
        self.assertEqual(self.line.pos, self.COL_NB)
        self.assertEqual(self.line.screen_pos, (1, 0))

        self.line.write('N')
        self.assertEqual(self.line.content, ['-' * self.COL_NB, 'N'])
        self.assertEqual(self.line.pos, self.COL_NB + 1)
        self.assertEqual(self.line.screen_pos, (1, 1))

    def test_fulllines(self):
        self.line.write('-' * self.COL_NB)
        self.assertEqual(self.line.content, ['-' * self.COL_NB])
        self.assertEqual(self.line.pos, self.COL_NB)
        self.assertEqual(self.line.screen_pos, (1, 0))

        self.line.write('N' * self.COL_NB)
        self.assertEqual(self.line.content, ['-' * self.COL_NB,
                                             'N' * self.COL_NB])
        self.assertEqual(self.line.pos, self.COL_NB * 2)
        self.assertEqual(self.line.screen_pos, (2, 0))

    def test_write_pos(self):
        self.line.write('1' * self.COL_NB + '2' * self.COL_NB)
        self.assertEqual(self.line.content, ['1' * self.COL_NB,
                                             '2' * self.COL_NB])

        self.line.update_pos(CursorPos.HOME)
        self.line.write('0')
        self.assertEqual(self.line.content, ['0' + '1' * (self.COL_NB - 1),
                                             '1' + '2' * (self.COL_NB - 1),
                                             '2'])
        self.assertEqual(self.line.pos, 1)
        self.assertEqual(self.line.screen_pos, (0, 1))

        self.line.update_pos(CursorPos.END)
        self.line.write('0')
        self.assertEqual(self.line.content, ['0' + '1' * (self.COL_NB - 1),
                                             '1' + '2' * (self.COL_NB - 1),
                                             '20'])
        self.assertEqual(self.line.pos, self.COL_NB * 2 + 2)
        self.assertEqual(self.line.screen_pos, (2, 2))

        self.line.update_pos(CursorPos.LEFT)
        self.assertEqual(self.line.pos, self.COL_NB * 2 + 1)
        self.assertEqual(self.line.screen_pos, (2, 1))
        self.line.write('1')
        self.assertEqual(self.line.content, ['0' + '1' * (self.COL_NB - 1),
                                             '1' + '2' * (self.COL_NB - 1),
                                             '210'])
        self.assertEqual(self.line.pos, self.COL_NB * 2 + 2)
        self.assertEqual(self.line.screen_pos, (2, 2))

        self.line.update_pos(CursorPos.RIGHT)
        self.line.update_pos(CursorPos.RIGHT)
        self.line.update_pos(CursorPos.RIGHT)
        self.assertEqual(self.line.pos, self.COL_NB * 2 + 3)
        self.line.write('1')
        self.assertEqual(self.line.content, ['0' + '1' * (self.COL_NB - 1),
                                             '1' + '2' * (self.COL_NB - 1),
                                             '2101'])
        self.assertEqual(self.line.pos, self.COL_NB * 2 + 4)
        self.assertEqual(self.line.screen_pos, (2, 4))

        self.line.update_pos(CursorPos.LEFT)
        self.line.update_pos(CursorPos.LEFT)
        self.line.update_pos(CursorPos.LEFT)
        self.line.update_pos(CursorPos.LEFT)
        self.line.update_pos(CursorPos.LEFT)
        self.line.update_pos(CursorPos.LEFT)
        self.line.update_pos(CursorPos.RIGHT)
        self.line.write('9')
        self.assertEqual(self.line.content, ['0' + '1' * (self.COL_NB - 1),
                                             '1' + '2' * (self.COL_NB - 2)
                                             + '9', '22101'])
        self.assertEqual(self.line.pos, self.COL_NB * 2)
        self.assertEqual(self.line.screen_pos, (2, 0))

        self.line.update_pos(CursorPos.END)
        self.assertEqual(self.line.pos, self.COL_NB * 2 + 5)
        self.assertEqual(self.line.screen_pos, (2, 5))

        self.line.update_pos(CursorPos.HOME)
        self.assertEqual(self.line.pos, 0)
        self.assertEqual(self.line.screen_pos, (0, 0))

    def test_write_full(self):
        for idx in range(1, self.LINE_NB + 11):
            self.line.write(str(idx % 10) * self.COL_NB)
        lines = self.line.get()
        self.assertEqual(len(lines), self.LINE_NB)
        self.assertEqual(lines[-1], str(self.LINE_NB % 10) * self.COL_NB)
        start = len(self.line.content) - self.LINE_NB + 1
        self.assertEqual(lines, [str(idx % 10) * self.COL_NB
                                 for idx in range(start, start + self.LINE_NB)])

    def test_del(self):
        self.line.delete()
        self.assertEqual(self.line.content, [])
        self.assertEqual(self.line.pos, 0)
        self.assertEqual(self.line.screen_pos, (0, 0))

    def test_del(self):
        self.line.write('1' * self.COL_NB + '2' * self.COL_NB + '34')
        self.assertEqual(self.line.content, ['1' * self.COL_NB,
                                             '2' * self.COL_NB,
                                             '34'])
        self.line.delete()
        self.assertEqual(self.line._content,
                         '1' * self.COL_NB + '2' * self.COL_NB + '3')
        self.assertEqual(self.line.content, ['1' * self.COL_NB,
                                             '2' * self.COL_NB,
                                             '3'])
        self.assertEqual(self.line.pos, self.COL_NB * 2 + 1)
        self.assertEqual(self.line.screen_pos, (2, 1))

        self.line.delete()
        self.assertEqual(self.line.content, ['1' * self.COL_NB,
                                             '2' * self.COL_NB])
        self.assertEqual(self.line.pos, self.COL_NB * 2)
        self.assertEqual(self.line.screen_pos, (2, 0))

        self.line.delete()
        self.assertEqual(self.line.content, ['1' * self.COL_NB,
                                             '2' * (self.COL_NB - 1)])
        self.assertEqual(self.line.pos, self.COL_NB * 2 - 1)
        self.assertEqual(self.line.screen_pos, (1, self.COL_NB - 1))

    def test_del_pos(self):
        self.line.write('1' * self.COL_NB + '2' * self.COL_NB)
        self.assertEqual(self.line.content, ['1' * self.COL_NB,
                                             '2' * self.COL_NB])
        self.line.update_pos(CursorPos.HOME)
        self.line.write('0')
        self.assertEqual(self.line.content, ['0' + '1' * (self.COL_NB - 1),
                                             '1' + '2' * (self.COL_NB - 1),
                                             '2'])
        self.assertEqual(self.line.pos, 1)
        self.assertEqual(self.line.screen_pos, (0, 1))

    def test_pos_out(self):
        self.line.write('1' * 4)
        self.line.update_pos(-10)
        self.assertEqual(self.line.pos, 0)
        self.line.update_pos(10)
        self.assertEqual(self.line.pos, 4)

    def test_del_all(self):
        self.line.write('1' * 4)
        self.line.delete(4)
        self.assertEqual(self.line.get(), [])

        self.line.write('1' * 4)
        self.line.delete(6)
        self.assertEqual(self.line.get(), [])

    def test_get(self):
        self.line.write('-' * self.COL_NB * (self.LINE_NB - 2))
        self.line.write('1' * self.COL_NB)
        self.line.write('2' * self.COL_NB)
        self.assertEqual(self.line.get(),
                         ['-' * self.COL_NB] * (self.LINE_NB - 2)
                         + ['1' * self.COL_NB]
                         + ['2' * self.COL_NB])
        self.assertEqual(self.line.get(3),
                         ['-' * self.COL_NB]
                         + ['1' * self.COL_NB]
                         + ['2' * self.COL_NB])

    def test_del_full(self):
        for idx in range(1, self.LINE_NB + 11):
            self.line.write(str(idx % 10) * self.COL_NB)
        self.assertEqual(self.line.pos, (self.LINE_NB + 10) * self.COL_NB)
        self.line.delete()
        lines = self.line.get()
        expected = []
        for idx in range(len(self.line.content) - self.LINE_NB + 1,
                         self.LINE_NB + 11):
            expected.append(str(idx % 10) * self.COL_NB)
        expected[-1] = expected[-1][:-1]
        self.assertEqual(lines[-1], str(self.LINE_NB % 10) * (self.COL_NB - 1))
        self.assertEqual(lines, expected)

        line1 = str((len(self.line.content) - self.LINE_NB) % 10) * self.COL_NB
        expected = [line1] + expected[:-1]
        expected[-1] = expected[-1][:-1]
        self.line.delete(self.COL_NB)
        lines = self.line.get()
        self.assertEqual(
            lines[-1], str((self.LINE_NB - 1) % 10) * (self.COL_NB - 1))
        self.assertEqual(lines, expected)

    def test_prompt(self):
        prompt = f'line {0:5}: '
        length = len(prompt)
        self.line = TermLine(self.LINE_NB, self.COL_NB)
        self.line.prompt_set()
        self.assertEqual(self.line.content, [prompt])
        self.assertEqual(len(self.line.content[0]), length)

        self.line.write('1' * self.COL_NB + '2' * self.COL_NB)
        expected = [prompt + '1' * (self.COL_NB - length),
                    '1' * length + '2' * (self.COL_NB - length),
                    '2' * length]
        self.assertEqual(len(''.join(self.line.content)),
                         len(''.join(expected)))
        self.assertEqual(self.line.content, expected)

        self.line.update_pos(CursorPos.HOME)
        self.assertEqual(self.line.pos, 0)
        self.assertEqual(self.line.screen_pos, (0, length))

        self.line.update_pos(CursorPos.LEFT)
        self.assertEqual(self.line.pos, 0)
        self.assertEqual(self.line.screen_pos, (0, length))

        self.line.update_pos(CursorPos.RIGHT)
        self.line.update_pos(CursorPos.LEFT)
        self.line.update_pos(CursorPos.LEFT)
        self.assertEqual(self.line.pos, 0)
        self.assertEqual(self.line.screen_pos, (0, length))

        self.line.update_pos(CursorPos.END)
        self.assertEqual(self.line.pos, 2 * self.COL_NB)
        self.assertEqual(self.line.screen_pos, (2, length))

        self.line.delete()
        self.assertEqual(self.line.pos, 2 * self.COL_NB - 1)
        self.assertEqual(self.line.screen_pos, (2, length - 1))
        self.assertEqual(self.line._content,
                         '1' * self.COL_NB + '2' * (self.COL_NB - 1))
        expected = [prompt + '1' * (self.COL_NB - length),
                    '1' * length + '2' * (self.COL_NB - length),
                    '2' * (length - 1)]
        self.assertEqual(self.line.content, expected)

        self.line.delete(10)
        self.assertEqual(self.line.pos, 2 * self.COL_NB - 11)
        self.assertEqual(self.line.screen_pos, (2, length - 11))
        self.assertEqual(self.line._content,
                         '1' * self.COL_NB  + '2' * (self.COL_NB - 11))
        expected = [prompt + '1' * (self.COL_NB - length),
                    '1' * length + '2' * (self.COL_NB - length),
                    '2' * (length - 11)]
        self.assertEqual(self.line.content, expected)



class MockWindow(Window):
    def __init__(self, lines, columns, posy, posx):
        def clear():
            self.line_buffer = [''] * self.lines
            self.posx = 0
            self.posy = 0

        def clrtoeol():
            line = self.line_buffer[self.posy]
            self.line_buffer[self.posy] = line[:self.posx]

        def clrtobot():
            self.logger.debug('Clearing from %d.%d', self.posy, self.posx)
            self.clrtoeol()
            for idx in range(self.posy + 1, self.lines):
                self.line_buffer[idx] = ''

        def move(posy, posx):
            self.logger.debug('Moving to %d.%d', posy, posx)
            self.posy = posy
            self.posx = posx

        self.logger = logging.getLogger('WindowMock')

        self.lines = lines
        self.columns = columns
        self.posy = posy
        self.posx = posx
        self.line_buffer = [''] * lines

        self.clear = unittest.mock.Mock(side_effect=clear)
        self.clrtoeol = unittest.mock.Mock(side_effect=clrtoeol)
        self.clrtobot = unittest.mock.Mock(side_effect=clrtobot)
        self.getch = unittest.mock.Mock(return_value='c')
        self.keypad = unittest.mock.Mock()
        self.move = unittest.mock.Mock(side_effect=move)
        self.refresh = unittest.mock.Mock()

    def __getattr__(self, attr):
        mock = unittest.mock.Mock()
        setattr(self, attr, mock)
        return mock

    def addstr(self, posy, posx, line, attr=None):
        self.logger.debug('Writing buffer at %dx%d: "%s"', posy, posx, line)
        if not line:
            return
        buf = self.line_buffer[posy][:posx] + line
        buf += self.line_buffer[posy][posx + len(line):]
        self.line_buffer[posy] = buf
        self.posy = posy + (posx + len(line)) // self.columns
        self.posx = (posx + len(line)) % self.columns
        self.logger.debug('Resulting pos %d.%d', self.posy, self.posx)

    def getbegyx(self):
        return self.posy, self.posx

    def getmaxyx(self):
        return self.lines, self.columns


class TestTermWindow(TestCommon):
    COLUMNS = 80
    LINES = 30
    POSX = 10
    POSY = 12

    @unittest.mock.patch('curses.newwin', new=MockWindow)
    def setUp(self):
        super().setUp()
        self.termwin = TermWindow('test', self.LINES, self.COLUMNS, self.POSY,
                                  self.POSX)
        self.termwin.prompt_enable()
        self.window = self.termwin.window
        if not isinstance(self.window, MockWindow):
            raise AssertionError('The window is not a MockWindow, but a %s' %
                                 self.termwin.window.__class__.__name__)
        self.window.keypad.assert_called_with(True)

    def test_read(self):
        self.termwin.read()
        self.window.getch.assert_called_once()

    def test_prompt(self):
        self.assertEqual(self.window.line_buffer, [''] * self.LINES)
        termline_prompt = self.termwin.line_create()
        self.termwin.write(termline_prompt)
        self.termwin.redraw()
        prompt = TermLine.PROMPT_FMT.format(1)
        self.assertEqual(self.window.line_buffer,
                         [prompt] + [''] * (self.LINES - 1))
        self.assertEqual(self.window.posy, 0)
        self.assertEqual(self.window.posx, len(prompt))
        self.window.refresh.assert_called_once()
        self.window.clrtobot.assert_called_once()

    def test_prompt_custom(self):
        prompt = 'custom prompt: '
        line = 'test prompt'
        termline = self.termwin.line_create(line, prompt=prompt)
        self.termwin.write(termline)
        self.termwin.redraw()
        self.assertEqual(self.window.line_buffer,
                         [prompt + line] + [''] * (self.LINES - 1))
        self.assertEqual(self.window.posy, 0)
        self.assertEqual(self.window.posx, len(prompt + line))

    def test_screen_empty(self):
        self.termwin.redraw()
        self.assertEqual(self.window.line_buffer, [''] * self.LINES)
        self.assertEqual(self.window.posy, 0)
        self.assertEqual(self.window.posx, 0)

    def test_one_line(self):
        prompt = TermLine.PROMPT_FMT.format(1)
        line = 'small line'
        self.termwin.write(self.termwin.line_create(line))
        self.termwin.redraw()
        self.assertEqual(self.window.line_buffer,
                         [prompt + line] + [''] * (self.LINES - 1))
        self.assertEqual(self.window.posy, 0)
        self.assertEqual(self.window.posx, len(prompt) + len(line))
        self.window.clear.assert_not_called()
        self.window.refresh.assert_called_once()

    def test_one_line_long_no_newprompt(self):
        prompt = TermLine.PROMPT_FMT.format(1)
        line = '-' * self.COLUMNS
        part = 'very long line'
        line += part + '-' * self.COLUMNS
        full_line = prompt + line
        self.termwin.write(self.termwin.line_create(line))
        self.termwin.redraw()
        self.assertEqual(self.window.line_buffer,
                         [full_line[:self.COLUMNS],
                          full_line[self.COLUMNS:self.COLUMNS * 2],
                          full_line[self.COLUMNS * 2:]]
                         + [''] * (self.LINES - 3))
        self.assertEqual(self.window.posy, 2)
        self.assertEqual(self.window.posx, len(prompt) + len(part))
        self.window.clear.assert_not_called()
        self.window.refresh.assert_called_once()

    def test_one_line_long_newprompt(self):
        prompt = TermLine.PROMPT_FMT.format(1)
        line = '-' * self.COLUMNS
        part = 'very long line'
        line += part + '-' * self.COLUMNS
        full_line = prompt + line
        self.termwin.write([self.termwin.line_create(line),
                            self.termwin.line_create(num=2)])
        self.termwin.redraw()
        self.assertEqual(self.window.line_buffer,
                         [full_line[:self.COLUMNS],
                          full_line[self.COLUMNS:self.COLUMNS * 2],
                          full_line[self.COLUMNS * 2:],
                          TermLine.PROMPT_FMT.format(2)]
                         + [''] * (self.LINES - 4))
        self.assertEqual(self.window.posy, 3)
        self.assertEqual(self.window.posx, len(prompt))
        self.window.clear.assert_not_called()
        self.window.refresh.assert_called_once()

    def test_one_line_full(self):
        prompt = TermLine.PROMPT_FMT.format(1)
        line = '-' * self.COLUMNS * (self.LINES + 2) + 'full content'
        self.termwin.write([self.termwin.line_create(line),
                            self.termwin.line_create(num=2)])
        self.termwin.redraw()
        self.assertEqual(
            self.window.line_buffer,
            ['-' * self.COLUMNS] * (self.LINES - 2)
            + ['-' * len(prompt) + 'full content',
               TermLine.PROMPT_FMT.format(2)])
        self.assertEqual(self.window.posy, self.LINES - 1)
        self.assertEqual(self.window.posx, len(prompt))
        self.assertEqual(self.window.clear.call_count, 1)
        self.window.refresh.assert_called_once()

    def test_multi_line(self):
        termlines = [self.termwin.line_create(str(idx), num=idx + 1)
                     for idx in range(self.LINES)] + [
                             self.termwin.line_create(num=self.LINES + 1)]
        self.termwin.write(termlines)
        self.termwin.redraw()
        self.logger.debug('BUFFER %s', self.termwin.window.line_buffer)

        buf = [TermLine.PROMPT_FMT.format(idx + 1) + str(idx)
               for idx in range(1, self.LINES)] + [
                       TermLine.PROMPT_FMT.format(self.LINES + 1)]

        self.assertEqual(self.window.line_buffer, buf)
        self.assertEqual(self.window.posy, self.LINES - 1)
        self.assertEqual(self.window.posx, len(TermLine.PROMPT_FMT.format(2)))
        self.assertEqual(self.window.clear.call_count, 1)
        self.window.refresh.assert_called_once()
        self.termwin.write(
            [self.termwin.line_create(str(idx)) for idx in range(self.LINES * 2)]
            + [self.termwin.line_create(num=self.LINES * 2 + 1)])
        self.termwin.redraw()
        self.assertEqual(self.window.clear.call_count, 2)

    def test_multi_lines(self):
        termlines = self.termwin.lines_get(
            [str(idx) for idx in range(self.LINES)] + [''])
        expects = (
            [self.termwin.line_create(str(idx))
             for idx in range(0, self.LINES)]
            + [self.termwin.line_create(num=self.LINES)])
        self.assertEqual(len(termlines), len(expects))
        self.assertEqual(termlines[-1], expects[-1])
        self.assertEqual(termlines, expects)

        self.termwin.write(termlines)
        self.termwin.redraw()
        self.logger.debug('BUFFER %s', self.termwin.window.line_buffer)

        buf = [TermLine.PROMPT_FMT.format(idx + 1) + str(idx)
               for idx in range(1, self.LINES)] + [
                       TermLine.PROMPT_FMT.format(self.LINES + 1)]

        self.assertEqual(self.window.line_buffer, buf)
        self.assertEqual(self.window.posy, self.LINES - 1)
        self.assertEqual(self.window.posx, len(TermLine.PROMPT_FMT.format(2)))
        self.assertEqual(self.window.clear.call_count, 1)
        self.window.refresh.assert_called_once()
        self.termwin.write(
            [self.termwin.line_create(str(idx)) for idx in range(self.LINES * 2)]
            + [self.termwin.line_create(num=self.LINES * 2 + 1)])
        self.termwin.redraw()
        self.assertEqual(self.window.clear.call_count, 2)

    def test_title(self):
        pass

    def test_line_str(self):
        self.termwin.prompt_enable(False)
        self.termwin.write('test')
        content, _ = self.termwin.queue.get()
        termline = TermLine(window_cols=self.termwin.dim[1],
                            window_lines=self.termwin.dim[0],
                            content='test')
        screenlines = ['test']
        self.assertEqual([(termline, screenlines)], content)


class CustomMagic(type):
    @classmethod
    def __getattr__(cls, attr):
        return unittest.mock.Mock()
        setattr(cls, attr, mock)
        return mock


class MockCurses(metaclass=CustomMagic):
    COLORS = 1
    cbreak = unittest.mock.Mock()
    echo = unittest.mock.Mock()
    initscr = unittest.mock.Mock(return_value=MockWindow(80, 30, 0, 0))
    ncurses_version = (0, 0, 42)
    newwin = unittest.mock.Mock(side_effect=MockWindow)
    noecho = unittest.mock.Mock()
    nocbreak = unittest.mock.Mock()
    A_BOLD = 1


class TestInterface(TestCommon):
    COLUMNS = 80
    LINES = 30

    def test_default(self):
        with unittest.mock.patch('pycom.term_win.curses',
                                 new=MockCurses) as MockedCurses:
            mocked_curses = MockedCurses()
            config = Config()
            config.interface_parse(cols=30, lines=20)
            interface = Interface(config)
            for window in config.interface:
                interface.window_add(**window)
            self.assertIn('command', interface.windows)
            self.assertIn('error', interface.windows)
            self.assertIn('serial', interface.windows)
            interface.screen.keypad.assert_called_once_with(True)
            mocked_curses.noecho.assert_called()
            mocked_curses.cbreak.assert_called()

            # interface.error.assert_called()
            # Ensure __del__ is called in this context, not with the real
            # curses module
            del interface
            mocked_curses.echo.assert_called()
            mocked_curses.nocbreak.assert_called()
