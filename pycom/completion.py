'''Basic completion implementation'''

import logging
import pprint
from typing import Any, Dict

__author__ = 'Jimmy Durand Wesolowski'
__copyright__ = 'Copyright (C) 2022 Jimmy Durand Wesolowski'
__license__ = 'GPL v2.0'
__version__ = '1.0'


class Completion:
    '''Class to do basic completion on the current command, based on a given
    configuration dictionary such as

    {
        "command_1": ["command_1_argument1", "command_1_argument2"],
        "command_2": {
            "command_2_subcommand_1": ["command_2_subcommand_1_arg1"],
            "command_2_subcommand_2": [],
        ...
    }
    '''
    def __init__(self, completion_dict: Dict[str, Any]):
        self.dictionary = completion_dict
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug('Completion loadded with %s',
                          pprint.pformat(self.dictionary))

    def search(self, line: str):
        '''Complete the line based on the current content "line"'''
        self.logger.debug('Calling completion search with "%s"', line)
        words = line.split(' ')
        if line and line[-1] == ' ':
            self.logger.info('Completing line "%s"', line)
            return line, self.entries(words)
        self.logger.info('Completing word "%s"', words[:-1])
        try:
            line, word = line.rsplit(' ')
            line += ' '
        except ValueError:
            word = line
            line = ''
        entries_all = self.entries(words[:-1])
        entries = [item for item in entries_all if item.startswith(word)]
        self.logger.debug('Matching "%s": "%s"', words[:-1], entries)
        return line, entries

    def _entries(self, dictionary, words):
        if not words:
            return dictionary.keys()
        try:
            return self._entries(dictionary[words[0]], words[1:])
        except KeyError:
            return dictionary.keys()

    def entries(self, words):
        '''Return all the possible entries from "words", e.g. based on the
        class documentation: entries("command_2 command_2_subcommand_1") will
        return
        ["command_2_subcommand_1_arg1"]
        '''
        return self._entries(self.dictionary, words)
