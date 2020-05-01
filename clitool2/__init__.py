'''Create CLI interface for an arbitrary function or callable object.

Usage:

Create a CLI interface for the greet function using the CLITool class.

def greet(name):
    """Greet person"""
    return "Hello %s!" % name

def main():
    """Entry point for application"""
    tool = CLITool(greet, parse_doc=True)
    result = tool()
    logging.info(result.output)
    sys.exit(result.status)
'''
from __future__ import absolute_import
from clitool2.clitool import CLITool, Result, DocInfo, parse_docstr
from clitool2.clitoolbox import CLIToolbox

__version__ = "1.1"
