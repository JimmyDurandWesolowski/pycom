import curses
import curses.ascii
import unittest
import unittest.mock

from tests.common import TestCommon
import pycom.command
from pycom.mode import Mode
from pycom.cursorpos import CursorPos
# import pycom.utils


class TestCommand(TestCommon):
    def setUp(self):
        self.terminal = unittest.mock.MagicMock()
        self.command = pycom.command.Command(self.terminal)

    def test_start_stop(self):
        self.command.start()
        self.terminal.assert_not_called()
        self.command.stop()
        self.terminal.assert_not_called()

    def test_backspace(self):
        self.command(curses.KEY_BACKSPACE)
        self.terminal.line_current.delete.assert_called_once_with(1)
        self.terminal.line_current.delete.reset_mock()

        self.terminal.mode_set(Mode.COMPLETION)
        self.command(curses.KEY_BACKSPACE)
        self.terminal.line_current.delete.assert_called_once_with(1)
        self.terminal.line_current.delete.reset_mock()

        self.terminal.mode_set(Mode.ESCAPE)
        self.command(curses.KEY_BACKSPACE)
        self.terminal.line_current.delete.assert_called_with(1)
        self.terminal.line_current.delete.reset_mock()

        self.terminal.mode_set(Mode.HISTORY)
        self.command(curses.KEY_BACKSPACE)
        self.terminal.line_current.delete.assert_called_with(1)
        self.terminal.line_current.delete.reset_mock()

        self.terminal.mode_set(Mode.SEARCH)
        self.command(curses.KEY_BACKSPACE)
        self.terminal.line_current.delete.assert_called_with(1)

    def test_eot(self):
        self.command(curses.ascii.EOT)
        self.terminal.terminate.assert_called_once()

    def test_history_browse(self):
        self.command(curses.KEY_UP)
        self.terminal.mode_set.assert_called_once_with(Mode.HISTORY)
        self.terminal.mode_set.reset_mock()

        self.command(curses.KEY_DOWN)
        self.terminal.mode_set.assert_not_called()

        command = pycom.command.CommandHistory(self.terminal)
        ret = command(curses.KEY_DOWN)
        self.assertTrue(ret)
        self.terminal.mode_set.assert_not_called()
        self.terminal.history.pos_update.assert_called_once_with(1)
        self.terminal.history.reset_mock()

        ret = command(curses.KEY_UP)
        self.assertTrue(ret)
        self.terminal.mode_set.assert_not_called()
        self.terminal.history.pos_update.assert_called_once_with(-1)
        self.terminal.history.reset_mock()

    def test_history_modify(self):
        command = pycom.command.CommandHistory(self.terminal)

        ret = command(ord('a'))
        self.assertTrue(ret)
        self.terminal.mode_set.assert_called_once_with(Mode.NORMAL)
        self.terminal.overwrite.assert_called_once_with(
            f'{self.terminal.history[0]}a')
        self.terminal.mode_set.reset_mock()
        self.terminal.history.reset_mock()
        self.terminal.overwrite.reset_mock()

        ret = command(ord('\n'))
        self.assertTrue(ret)
        self.terminal.mode_set.assert_called_once_with(Mode.NORMAL)
        self.terminal.overwrite.assert_called_once_with(
            str(self.terminal.history.line_current))
        self.terminal.mode_set.reset_mock()
        self.terminal.history.reset_mock()
        self.terminal.overwrite.reset_mock()

        ret = command(curses.KEY_BACKSPACE)
        self.assertTrue(ret)
        self.terminal.mode_set.assert_called_once_with(Mode.NORMAL)
        self.terminal.overwrite.assert_called_once_with(
            str(self.terminal.history.line_current))
        self.terminal.history.line_current.delete.assert_not_called()
        self.terminal.line_current.delete.assert_called_once_with(1)
        self.terminal.mode_set.reset_mock()
        self.terminal.history.reset_mock()
        self.terminal.overwrite.reset_mock()

    def test_history_unimplemented(self):
        command = pycom.command.CommandHistory(self.terminal)
        ret = command(0x80)
        self.assertFalse(ret)
        self.terminal.mode_set.reset_mock()
        self.terminal.history.reset_mock()
        self.terminal.overwrite.reset_mock()

    def test_history_entries(self):
        command = pycom.command.CommandHistory(self.terminal)
        self.terminal.history.pos_update = unittest.mock.MagicMock(return_value=True)

        ret = command(curses.KEY_UP)
        self.assertTrue(ret)
        self.terminal.mode_set.assert_not_called()

        ret = command(curses.KEY_DOWN)
        self.assertTrue(ret)
        self.terminal.mode_set.assert_not_called()

        self.terminal.history.pos_update = unittest.mock.MagicMock(return_value=False)

        ret = command(curses.KEY_UP)
        self.assertTrue(ret)
        self.terminal.mode_set.assert_called_once_with(Mode.NORMAL)
        self.terminal.mode_set.reset_mock()

        ret = command(curses.KEY_DOWN)
        self.assertTrue(ret)
        self.terminal.mode_set.assert_called_once_with(Mode.NORMAL)

    def test_history_start(self):
        command = pycom.command.CommandHistory(self.terminal)
        command.start()
        self.terminal.history.reset.assert_called_once_with()

    def test_line_append(self):
        self.terminal.line_current.__iadd__.return_value = self.terminal.line_current
        self.command(ord('a'))
        self.terminal.line_current.__iadd__.assert_called_once_with('a')
        self.terminal.line_current.__iadd__.reset_mock()

        self.command(ord(' '))
        self.terminal.line_current.__iadd__.assert_called_once_with(' ')
        self.terminal.line_current.__iadd__.reset_mock()

        self.command(ord('\n'))
        self.terminal.line_current.__iadd__.assert_not_called()
        self.terminal.line_current.__iadd__.reset_mock()

        self.command(curses.KEY_RIGHT)
        self.terminal.line_current.__iadd__.assert_not_called()

    def test_line_pos(self):
        self.command(curses.KEY_LEFT)
        self.terminal.pos_update.assert_called_once_with(CursorPos.LEFT)

        self.command(curses.KEY_RIGHT)
        self.terminal.pos_update.assert_called_with(CursorPos.RIGHT)

        self.command(curses.KEY_HOME)
        self.terminal.pos_update.assert_called_with(CursorPos.HOME)

        self.command(curses.KEY_END)
        self.terminal.pos_update.assert_called_with(CursorPos.END)

    def test_newline(self):
        self.command(curses.ascii.NL)
        self.terminal.newline.assert_called_once()
        self.terminal.newline.reset_mock()

        self.command(ord('\n'))
        self.terminal.newline.assert_called_once()
        self.terminal.newline.reset_mock()

        self.command(ord('\r'))
        self.terminal.newline.assert_called_once()
        self.terminal.newline.reset_mock()

    def test_partially_implemented(self):
        def partial_implementation(key):
            return False
        self.command.logger = unittest.mock.Mock()
        with unittest.mock.patch.dict(self.command._map,
                                      {256: partial_implementation}):
            self.command(256)
            self.terminal.interface.write.assert_called_once_with('error',
                'Line functionality 256 not fully implemented yet')
            self.command.logger.warning.assert_called_once_with(
                'Command %s not fully implemented', 256)

    def test_search(self):
        # FIXME: Not implemented yet
        print('Search not implemented yet')
        return
        self.command(curses.ascii.DC2)
        self.terminal.mode_set.assert_called_once_with(Mode.SEARCH)
        self.assertTrue(self.command.is_command(ord('s')))
        self.assertTrue(self.command.is_command(ord('e')))
        self.assertTrue(self.command.is_command(ord('a')))
        self.assertTrue(self.command.is_command(ord('r')))
        self.assertTrue(self.command.is_command(ord('c')))
        self.assertTrue(self.command.is_command(ord('h')))
        self.command(curses.ascii.NL)
        self.terminal.newline.assert_called_once()
        self.assertFalse(self.command.is_command(ord('s')))

    def test_tab(self):
        # FIXME: Not implemented yet
        print('Completion not implemented yet')
        return
        self.command(curses.ascii.TAB)
        self.terminal.completion.assert_called_once()

    def test_unimplemented(self):
        self.command.logger = unittest.mock.Mock()
        self.command(curses.ascii.RS)
        self.terminal.interface.write.assert_called_once_with('error',
            'Line functionality RS - Record separator, block-mode terminator '
            '(30) not implemented yet')
        self.command.logger.warning.assert_called_once_with(
            'Command %s not implemented', 30)
        self.terminal.interface.write.reset_mock()

        self.command(256)
        self.terminal.interface.write.assert_called_once_with('error',
            'Line functionality 256 not implemented yet')
        self.command.logger.warning.assert_called_with(
            'Command %s not implemented', 256)
