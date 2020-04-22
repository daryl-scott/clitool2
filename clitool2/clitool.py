'''Create CLI interface for the supplied function or callable object

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
from __future__ import division
from __future__ import print_function
from argparse import ArgumentParser
from collections import namedtuple, OrderedDict
from itertools import takewhile
import datetime
import inspect
import json
import logging
import os
import re
import sys
from traceback import format_exc
from dateutil.parser import parse as to_date

# Updated on June 4, 2019 to emit trace entries at the debug level.
# Update on August 31, 2019 to remove dependency on arcpy.
__version__ = "1.0"

# Result provides information from a wrapped function
Result = namedtuple("Result", ("status", "output", "error"))

# DocInfo represents the results from parsing a Google style docstring
DocInfo = namedtuple("DocInfo", ("summary", "description", "args", "returns", "yields", "raises"))

def _to_bool(text):
    """Convert str value to bool.

    Returns True if text is "True" or "1" and False if text is "False" or "0".

    Args:
        text: str value

    Returns:
        bool
    """
    if text.title() in ("True", "1"):
        result = True
    elif text.title() in ("False", "0"):
        result = False
    else:
        raise ValueError("Expected 'True', 'False', '1', '0'; got '%s'" % text)

    return result

def _parse_docargs(text):
    """Parse the supplied text and return OrderedDict that maps parameter names
    to descriptions.

    Args:
        text: Args section of a Google style docstring.

    Returns:
        dict: OrderedDict that maps parameter names to descriptions.
    """
    pattern = r"^(\w+):(.+)$"
    prog = re.compile(pattern)
    result = OrderedDict()
    name = None

    for line in text.splitlines():
        match = prog.match(line)

        if match:
            # If line matches regex pattern, then add match results to dict.
            name = match.group(1)
            desc = match.group(2).strip()
            result[name] = desc
        elif name:
            # If line does not match regex pattern, then append line to
            # previous argument description.
            result[name] += " " + line.strip()
        else:
            raise ValueError("Expected name: value pair; got '%s'" % line)

    return result

def _config_parser(parser, func, func_help=None):
    """Update parser to be compatible with the supplied function.

    This function supports positional arguments, keyword arguments,
    var-positional, and var-keyword. var-keywords are added as an
    optional argument that supports JSON string.

    Args:
        parser: ArgumentParser object
        func: target function
        func_help: dict mapping parameter name to their description

    Returns:
        object: ArgumentParser
    """
    # A short option is one character long.
    # Note: inspect.getargspec() is deprecated since Python 3.0.
    if hasattr(inspect, "getfullargspec"):
        args, varargs, keywords, defaults = inspect.getfullargspec(func)[:4]
    else:
        args, varargs, keywords, defaults = inspect.getargspec(func)

    func_help = func_help or {}
    defaults = defaults or []
    required = args[:len(args) - len(defaults)]
    optional = list(zip(args[len(args) - len(defaults):], defaults))

    # Positional arguments have no default value.
    for arg in required:
        if arg == "self":
            continue
        text = func_help.get(arg, None)
        parser.add_argument(arg, help=text)

    # Optional arguments have default value.
    # Modified on 11/9/2017 to improve handling of default value type.
    # https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse
    for name, default in optional:
        argname = "-" + name if len(name) == 1 else "--" + name
        text = func_help.get(name, None)

        if isinstance(default, bool):
            type_ = _to_bool
        elif isinstance(default, int):
            type_ = int
        elif isinstance(default, float):
            type_ = float
        elif isinstance(default, datetime.datetime):
            type_ = to_date
        else:
            type_ = None

        parser.add_argument(argname, default=default, help=text, type=type_)

    # varargs support multiple values.
    if varargs:
        text = func_help.get(varargs, None)
        parser.add_argument(varargs, help=text, nargs="*")

    # keywords support key-value pairs supplied as json string
    if keywords:
        argname = "-" + keywords if len(keywords) == 1 else "--" + keywords
        text = func_help.get(keywords, None)
        parser.add_argument(argname, help=text, type=json.loads)

    return parser

def _getcallargs(func, **kwargs):
    """Transform parsed command line arguments to be compatible with function
    that may have var-positional and var-argument parameters.

    Args:
        func: target function
        kwargs: dict of argument name and values

    Returns:
        tuple: (args, kwargs)
    """
    # This method was developed to support varargs and keywords since the
    # results from parse_arguments cannot be passed directly to function.
    # Note: inspect.getargspec() is deprecated since Python 3.0.
    if hasattr(inspect, "getfullargspec"):
        names, varargs, keywords, defaults = inspect.getfullargspec(func)[:4]
    else:
        names, varargs, keywords, defaults = inspect.getargspec(func)

    defaults = defaults or []
    optional = list(zip(names[len(names) - len(defaults):], defaults))
    funcargs, funckwargs = [], {}

    for name in names:
        if name == "self":
            pass
        elif name in kwargs:
            funcargs.append(kwargs[name])
        elif name in optional:
            funcargs.append(optional[name])
        else:
            raise ValueError("No value available for '{0}'".format(name))

    if varargs and varargs in kwargs:
        items = kwargs[varargs]

        if isinstance(items, (tuple, list)):
            funcargs.extend(items)
        else:
            raise TypeError("Expected sequence; got %s" % type(items).__name__)

    if keywords and keywords in kwargs:
        mapping = kwargs[keywords]

        if mapping is None:
            pass
        elif isinstance(mapping, dict):
            funckwargs.update(mapping)
        else:
            raise TypeError("Expected dict; got %s" % type(mapping).__name__)

    return funcargs, funckwargs

def parse_docstr(text):
    """Parse Google style docstring and return DocInfo object.

    The sections consist of Summary (no heading), Description (no heading),
    Args, Returns, Yields, and Raises.  All sections are optional, but the
    sections must be in correct order for successful parsing.

    Args:
        text: Google style docstring

    Returns:
        namedtuple: DocInfo(summary, description, args, returns, yields, raises)
    """
    lines = [line.strip() for line in text.strip().splitlines()]
    sections = DocInfo._fields
    scratch = {}

    # test is used to detect section break
    test = lambda line: line.lower().rstrip(":") not in sections

    for section in sections:
        matches = []

        if section == "summary":
            if len(lines) == 1 or lines[1] == "":
                matches = lines[0:1]
        elif section == "description":
            matches = [line for line in takewhile(test, lines)]
        elif lines and lines[0] == section.title() + ":":
            del lines[0]
            matches = [line for line in takewhile(test, lines)]

        if matches:
            del lines[:len(matches)]
            value = os.linesep.join(matches)
            scratch[section] = value.strip()
        else:
            scratch[section] = None

    return DocInfo(**scratch)

def config_logging(logfile=None, logwrite=None, loglevel=20):
    """Configure logging to emit messages to the console and optional log files.

    Args:
        logfile: log file name; file is opened in append mode.
        logwrite: log file name; file is opened in write mode.
        loglevel: logging level; default is 20 (logging.INFO).
    """
    stream_format = "[%(levelname)s] %(message)s"
    file_format = "[%(asctime)s][%(levelname)s] %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    logger = logging.getLogger()
    logger.setLevel(logging.NOTSET)

    if not logger.handlers:
        # Add Stream Handler
        stream_formatter = logging.Formatter(stream_format, date_format)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(stream_formatter)
        stream_handler.setLevel(loglevel)
        logger.addHandler(stream_handler)

        if logfile:
            # Add File Handler (append)
            logfile_formatter = logging.Formatter(file_format, date_format)
            logfile_handler = logging.FileHandler(logfile, mode="a")
            logfile_handler.setFormatter(logfile_formatter)
            logfile_handler.setLevel(loglevel)
            logger.addHandler(logfile_handler)

        if logwrite:
            # Add File Handler (write)
            logwrite_formatter = logging.Formatter(file_format, date_format)
            logwrite_handler = logging.FileHandler(logwrite, mode="w")
            logwrite_handler.setFormatter(logwrite_formatter)
            logwrite_handler.setLevel(loglevel)
            logger.addHandler(logwrite_handler)

class CLITool(object):
    """Create CLI interface for the supplied function or callable object.

    The default implementation adds logging capability and options as configured
    by the logging manager function. The logging behavior can be modified by
    setting the logmngr argument to an alternative function.

    Attributes:
        func: Target function
        label: Text to include in the help message and start log message.
        description: Additional text to include in the help message.
        func_help: Dictionary mapping parameter names to descriptions.
        parse_doc: If True, parse Google style docstring for label,
            description, and func_help.
        logmngr: Logging manager function.
        parser: ArgumentParser object
    """
    def __init__(self, func, label=None, description=None, func_help=None, parse_doc=False,
                 logmngr=None):
        self.func = func
        self.label = label
        self.description = description or label
        self.func_help = func_help
        self.parse_doc = parse_doc
        self.logmngr = logmngr or config_logging
        self._parser = None

    @property
    def parser(self):
        """ArgumentParser object"""
        if not self._parser:
            if self.parse_doc:
                # Parse the function docstring; parameters take precedent over docstring
                parsed = parse_docstr(inspect.getdoc(self.func))
                label = self.label or parsed.summary
                description = self.description or parsed.description

                if not self.func_help and parsed.args:
                    func_help = _parse_docargs(parsed.args)
                else:
                    func_help = self.func_help
            else:
                label = self.label
                description = self.description
                func_help = self.func_help

            # Create parser
            parser = ArgumentParser(description=label, epilog=description,
                                    fromfile_prefix_chars="@")

            # Add arguments for the target function
            _config_parser(parser, self.func, func_help)

            # Add arguments for the logging manager function
            parsed = parse_docstr(inspect.getdoc(self.logmngr))

            if parsed.args:
                func_help = _parse_docargs(parsed.args)
            else:
                func_help = None

            # Create a group for the logging arguments
            group = parser.add_argument_group("logging arguments")
            _config_parser(group, self.logmngr, func_help)
            self._parser = parser

        return self._parser

    def execute(self, *args, **kwargs):
        """Execute function and return Result object"""
        try:
            status, output, error = 0, None, None
            datefmt = "%Y-%m-%d %H:%M:%S"
            start = datetime.datetime.now()

            # Construct and emit start message
            if self.label:
                logging.info(self.label)

            logging.info("Start Time: %s", start.strftime(datefmt))

            # Call wrapped function
            output = self.func(*args, **kwargs)
##        except arcpy.ExecuteError:
##            # Log arcpy error message
##            exc_type = "ExecuteError"
##            exc_value = arcpy.GetMessages(2) or "Unspecified error"
##            exc_tb = sys.exc_info()[2]
##            logging.error("%s: %s", exc_type, exc_value)
##            logging.debug(format_exc(exc_tb))
##            status = 1
        except Exception:
            # Emit error messages
            error = sys.exc_info()
            logging.error("%s: %s", error[0].__name__, error[1])
            logging.debug(format_exc())
            status = 1
        finally:
            # Construct and emit end message
            # Modified on 2/12/2016 to use '\n' instead of '\r\n' to create new line.
            # With '\r\n', the log file contained a mix of 'r' and '\r\n' line terminators.
            end = datetime.datetime.now()
            elapsed = str(end - start)[:-4]

            if status == 0:
                closing = "SUCCEEDED at %s (Elapsed Time: %s)\n"
            else:
                closing = "FAILED at %s (Elapsed Time: %s)\n"

            logging.info(closing, end.strftime(datefmt), elapsed)

        # Return result object
        return Result(status, output, error)

    def __call__(self, *args):
        """Parse command line arguments, execute callable, and return Result object"""
        # Parse arguments
        args = args or sys.argv[1:]
        params = vars(self.parser.parse_args(args))

        # Separate logging from func arguments
        logargs, logkwargs = _getcallargs(self.logmngr, **params)
        execargs, execkwargs = _getcallargs(self.func, **params)

        # Configure logging and call targt function
        self.logmngr(*logargs, **logkwargs)
        result = self.execute(*execargs, **execkwargs)
        logging.shutdown()

        return result
