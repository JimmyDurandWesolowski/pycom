'''Collection of '''

import collections
import curses.ascii
import json
import logging
import operator
import os
from typing import TYPE_CHECKING, Any, Optional, Sequence, Union

__author__ = 'Jimmy Durand Wesolowski'
__copyright__ = 'Copyright (C) 2022 Jimmy Durand Wesolowski'
__license__ = 'GPL v2.0'
__version__ = '1.0'


if TYPE_CHECKING:
    from _typeshed import SupportsRead  # pragma: no cover (type checking)


FileType = Union[Union[str, bytes, os.PathLike], int]
OptionalFileOrFilename = Optional[Union[str, 'SupportsRead[str]']]

ASCII_MAP = {
    curses.ascii.NUL: "NUL - NUL",
    curses.ascii.SOH: "SOH - Start of heading, console interrupt",
    curses.ascii.STX: "STX - Start of text",
    curses.ascii.ETX: "ETX - End of text",
    curses.ascii.EOT: "EOT - End of transmission",
    curses.ascii.ENQ: "ENQ - Enquiry, goes with ACK flow control",
    curses.ascii.ACK: "ACK - Acknowledgement",
    curses.ascii.BEL: "BEL - Bell",
    curses.ascii.BS: "BS - Backspace",
    curses.ascii.TAB: "TAB - Tab",
    curses.ascii.HT: "HT - Alias for TAB: “Horizontal tab”",
    curses.ascii.LF: "LF - Line feed",
    curses.ascii.NL: "NL - Alias for LF: “New line”",
    curses.ascii.VT: "VT - Vertical tab",
    curses.ascii.FF: "FF - Form feed",
    curses.ascii.CR: "CR - Carriage return",
    curses.ascii.SO: "SO - Shift-out, begin alternate character set",
    curses.ascii.SI: "SI - Shift-in, resume default character set",
    curses.ascii.DLE: "DLE - Data-link escape",
    curses.ascii.DC1: "DC1 - XON, for flow control",
    curses.ascii.DC2: "DC2 - Device control 2, block-mode flow control",
    curses.ascii.DC3: "DC3 - XOFF, for flow control",
    curses.ascii.DC4: "DC4 - Device control 4",
    curses.ascii.NAK: "NAK - Negative acknowledgement",
    curses.ascii.SYN: "SYN - Synchronous idle",
    curses.ascii.ETB: "ETB - End transmission block",
    curses.ascii.CAN: "CAN - Cancel",
    curses.ascii.EM: "EM - End of medium",
    curses.ascii.SUB: "SUB - Substitute",
    curses.ascii.ESC: "ESC - Escape",
    curses.ascii.FS: "FS - File separator",
    curses.ascii.GS: "GS - Group separator",
    curses.ascii.RS: "RS - Record separator, block-mode terminator",
    curses.ascii.US: "US - Unit separator",
    curses.ascii.SP: "SP - Space",
    curses.ascii.DEL: "DEL - Delete",
    curses.KEY_UP: 'KEY_UP',
    curses.KEY_DOWN: 'KEY_DOWN',
    curses.KEY_LEFT: 'KEY_LEFT',
    curses.KEY_RIGHT: 'KEY_RIGHT',
    curses.KEY_HOME: 'KEY_HOME',
    curses.KEY_END: 'KEY_END',
    curses.KEY_BACKSPACE: 'KEY_BACKSPACE',
}


def chunks(lst: Sequence,
           num: int) -> collections.abc.Iterator:
    '''Yield successive num-sized chunks from lst.
    source: https://stackoverflow.com/a/312464
    '''
    for i in range(0, len(lst), num):
        yield lst[i:i + num]


def _dict_update_rec(dict1: dict, dict2: dict) -> Any:
    '''Recursively add or update dict1 with dict2'''
    try:
        for key, value in dict2.items():
            if key in dict1:
                dict1[key] = _dict_update_rec(dict1[key], value)
                continue
            dict1[key] = value
        return dict1
    except (AttributeError, ValueError):
        return dict2


def dict_update_deep(dict1: dict, dict2: dict) -> dict:
    '''Update in place a dictionary 'dict1' key values for keys that exist or
    add the missing ones. Returns the updated 'dict1'.
    '''
    return _dict_update_rec(dict1, dict2)


def logging_level(verbose_count: Optional[int] = None):
    '''Set the root logger level according to the verbose count:
    0: warning, 1: info, 2 or higher: debug
    '''
    logger = logging.getLogger()
    if not verbose_count:
        logger.setLevel(logging.WARNING)
    elif verbose_count == 1:
        logger.setLevel(logging.INFO)
    elif verbose_count >= 2:
        logger.setLevel(logging.DEBUG)


def project_load_json(filename: str, toolname: Optional[str] = None,
                      default: Any = None):
    '''Load a project JSON file from .config/<toolname> (relative path) or the
    given absolute path and returns it as a dictionary.
    '''
    if os.path.isabs(filename) or toolname is None:
        path = filename
    else:
        path = os.path.join(os.environ['HOME'], '.config', toolname, filename)
    try:
        with open(path, encoding='utf-8') as file_fd:
            return json.load(file_fd)
    except (FileNotFoundError, OSError):
        return default


# Inspired from
# https://stackoverflow.com/a/43837429
# and simplified for our use-case
MATH_OPERATORS = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.truediv,
    '//': operator.floordiv,
}
MATH_OPERATOR_PIORITY = ['*', '/', '//', '+', '-']


def _parse_math_simple(expr, operators):
    try:
        val = int(expr)
        return val
    except ValueError:
        pass
    try:
        curop = operators[-1]
        func = MATH_OPERATORS[curop]
    except (KeyError, IndexError):
        return None
    elts = expr.split(curop)
    if len(elts) == 1:
        return _parse_math_simple(expr, operators[:-1])
    elts = [_parse_math_simple(elt, operators[:-1]) for elt in elts]
    return [func, elts]


def _eval_math_simple(content):
    val = 0
    try:
        func, elts = content
    except TypeError:
        return content
    vals = [_eval_math_simple(elt) for elt in elts]
    ret = vals[0]
    for val in vals[1:]:
        ret = func(ret, val)
    return ret


def eval_math_simple(expr):
    '''Safely evaluate the given math expression without using external
    library
    '''
    parsed = _parse_math_simple(expr, MATH_OPERATOR_PIORITY)
    return _eval_math_simple(parsed)
