"""Test Case for the clitoolbox module"""
from __future__ import absolute_import
import logging
from unittest import TestCase
from clitool2 import CLITool, CLIToolbox

def _add(num1, num2):
    """Add two numbers"""
    result = float(num1) + float(num2)
    logging.info("%s + %s = %s", num1, num2, result)
    return result

def _subtract(num1, num2):
    """Subtract two numbers"""
    result = float(num1) - float(num2)
    logging.info("%s - %s = %s", num1, num2, result)
    return result

class CLIToolboxTestCase(TestCase):
    """Test Case for the clitoolbox module"""
    def test_clitoolbox(self):
        """Test the CLIToolbox class"""
        toolbox = CLIToolbox()
        toolbox.add_command(CLITool(_add), "add")
        toolbox.add_command(CLITool(_subtract), "subtract")

        args1 = ("add", "10", "20")
        args2 = ("subtract", "20", "1")

        result1 = toolbox(*args1)
        result2 = toolbox(*args2)

        self.assertEqual(result1.output, 30)
        self.assertEqual(result2.output, 19)
