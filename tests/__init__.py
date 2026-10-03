import unittest

from .breeze_test import BreezeApiTestCase


def all_tests():
    suite = unittest.TestSuite()
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(BreezeApiTestCase))
    return suite
