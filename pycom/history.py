'''Basic terminal command history implementation'''

import collections
import logging
import os
from typing import List, Optional, Union

from pycom.utils import FileType

# pylint: disable=duplicate-code
__author__ = 'Jimmy Durand Wesolowski'
__copyright__ = 'Copyright (C) 2022 Jimmy Durand Wesolowski'
__license__ = 'GPL v2.0'
__version__ = '1.0'


class History(collections.UserList):
    '''Terminal command history class'''
    PROMPT = 'History {:5}: '

    class Error(Exception):
        '''History specific error'''

    def __init__(self, *data: List):
        self.history_file: Optional[FileType] = None
        self.history_save: bool = False
        self.pos: int = 0
        self.logger = logging.getLogger(self.__class__.__name__)
        super().__init__(*data)
        self.reset()

    def append(self, item: str) -> None:
        if not item:
            return
        self.logger.debug('Adding "%s"', item)
        updated = False
        try:
            pos = self.data.index(item)
            if pos != len(self.data) - 1:
                self.logger.debug(
                    '"%s" already in history at %d, updating its position',
                    item, pos)
                del self.data[pos]
                updated = True
            else:
                self.logger.debug('"%s" already in history', item)
        except ValueError:
            updated = True
        if not updated:
            return
        self.data.append(item)
        self.reset()
        self.save()

    @property
    def line_current(self) -> Union[str, None]:
        '''The currently selected history line, None if none is selected or
        the index is incorrect
        '''
        try:
            return self[self.pos]
        except IndexError:
            return None

    def pos_update(self, shift: int) -> bool:
        '''Updates the position of the history by the positive or negative
        given "shift".
        Returns True if the position is not further than the history size
        '''
        self.logger.debug('History shift by %d', shift)
        self.pos += shift
        if self.pos < 0:
            self.pos = 0
            return True
        if self.pos >= len(self):
            self.pos = max(0, len(self) - 1)
            return False
        self.logger.debug('History idx at %d/%d', self.pos, len(self) - 1)
        return True

    def load(self, history_save: bool = True,
             history_file: FileType = None) -> None:
        '''Load the history from the file "history_file". If the history should
        not be saved, "history_save" should be set to False
        '''
        if history_file is None:
            history_file = os.path.join(os.environ['HOME'], '.pycom_history')
        self.history_save = history_save
        self.history_file = history_file
        if not self.history_save:
            return
        try:
            with open(self.history_file, encoding='ascii') as history_fd:
                lines = [line.rstrip() for line in history_fd.readlines()]
        except (FileNotFoundError, OSError) as exc:
            raise self.Error(exc)
        self.data += [line for line in lines if line]
        self.logger.debug('History loaded:%s%s', os.linesep, os.linesep.join(
            [f'  "{line}"' for line in self.data]))
        self.reset()

    def reset(self) -> None:
        '''Reset the history position to the default value'''
        self.pos = len(self) - 1

    def save(self) -> None:
        '''Save the history, which will happen only if a file was given during
        "load", and "history_save" was not set to False
        '''
        if not self.history_save or self.history_file is None:
            return
        content = ''.join([f'{entry}{os.linesep}' for entry in self.data])
        try:
            with open(self.history_file, 'wt', encoding='ascii') as history_fd:
                history_fd.write(content)
        except (FileNotFoundError, OSError) as exc:
            raise self.Error(exc)

    def search(self, content: str) -> List[str]:
        '''Search the history entries matching "content"'''
        raise NotImplementedError
