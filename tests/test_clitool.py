"""Test Case for the clitool module"""
from __future__ import absolute_import
import inspect
import os
from unittest import TestCase
from clitool2 import CLITool, parse_docstr

def _test1(param1, param2, *args, **kwargs):
    """Sample function for TestCase.

    Returns the supplied values.

    Args:
        param1: parameter 1
        param2: parameter 2
        args: var-positional
        kwargs: JSON-encoded string

    Returns:
        tuple: (param1, param2, args, kwargs
    """
    return (param1, param2, args, kwargs)

def _test2(num1, num2):
    """Sample function for TestCase.

    Returns the supplied values.

    Args:
        num1: number 1
        num2: number 2

    Returns:
        float: sum of number 1 and 2
    """
    return float(num1) + float(num2)

class CLIToolTestCase(TestCase):
    """Test Case for the clitool module"""
    def test_parse_docstr(self):
        """Test for the parse_docstr function"""
        expected = ["param1: parameter 1", "param2: parameter 2",
                    "args: var-positional", "kwargs: JSON-encoded string"]

        info = parse_docstr(inspect.getdoc(_test1))
        self.assertEqual(info.summary, "Sample function for TestCase.")
        self.assertEqual(info.description, "Returns the supplied values.")
        self.assertEqual(info.args, os.linesep.join(expected))
        self.assertEqual(info.returns, "tuple: (param1, param2, args, kwargs")

    def test_clitool_normal(self):
        """Test the CLITool class with normal exit"""
        tool = CLITool(_test1, parse_doc=False)
        args = ("A", "B", "C", "D", '--kwargs={"E": 5}')
        expected = ("A", "B", ("C", "D"), {"E": 5})
        result = tool(*args)
        self.assertEqual(result.output, expected)
        self.assertEqual(result.status, 0)

    def test_clitool_error(self):
        """Test the CLITool class with exception in wrapped function"""
        tool = CLITool(_test2, parse_doc=True)
        args = ("1", "b")
        result = tool(*args)
        self.assertEqual(result.error[0], ValueError)
        self.assertEqual(result.status, 1)
