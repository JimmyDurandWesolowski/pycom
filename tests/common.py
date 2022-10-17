import logging
import os
import unittest


logging.basicConfig()

class TestCommon(unittest.TestCase):
    def setUp(self):
        super().setUp()
        try:
            logging.getLogger().setLevel(os.environ['LOGLEVEL'])
        except KeyError:
            pass
        self.logger = logging.getLogger(self.__class__.__name__)
