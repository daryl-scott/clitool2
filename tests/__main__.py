"""Execute tests for the clitool2 package"""
from __future__ import absolute_import
import unittest
from . import CLIToolTestCase
from . import CLIToolboxTestCase

def run_tests():
    """Execute tests for the clitool2 package"""
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    suite.addTest(loader.loadTestsFromTestCase(CLIToolTestCase))
    suite.addTest(loader.loadTestsFromTestCase(CLIToolboxTestCase))
    runner = unittest.TextTestRunner()
    runner.run(suite)

if __name__ == '__main__':
    run_tests()
