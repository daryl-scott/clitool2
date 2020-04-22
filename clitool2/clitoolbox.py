"""Command line interface for multiple commands"""
from __future__ import absolute_import, division, print_function
from argparse import ArgumentParser
import inspect
import sys
from clitool2.clitool import parse_docstr, Result

__version__ = "1.0"

def _format_epilog(commands):
    """Create a epilog string for the specified commands.

    Args:
        commands: Sequence of (func, name, description)

    Returns:
        str: Formatted list of commands and their descriptions
    """
    lines = []
    lines.append("Commands:")

    for command in commands:
        # Note: desc may be None or wrapped lines
        name = command[1]
        desc = command[2] or " "

        for index, item in enumerate(desc.splitlines()):
            item = item.strip()

            if index == 0:
                line = "  %-16s%s" % (name, item)
            else:
                line = " " * 18 + item

            lines.append(line)

    return '\r\n'.join(lines)

class CLIToolbox(object):
    """Provides a command line interface for multiple commands.

    Attributes:
        description: Text to display before the argument help
    """
    def __init__(self, description=None):
        self.description = description
        self._parser = None
        self._commands = []

    @property
    def parser(self):
        """ArgumentParser object"""
        if self._parser is None:
            parser = ArgumentParser(description=self.description, add_help=False,
                                    fromfile_prefix_chars="@")
            choices = [item[1] for item in self._commands]
            parser.add_argument("subcommand", choices=choices, nargs="?")
            self._parser = parser

        return self._parser

    def add_command(self, func, name, description=None, parse_doc=False):
        """Add command to toolbox.

        func can be a CLITool object, function, or callable object that accepts
        command line arguments and returns a Result object or status code.

        Args:
            func: CLITool object, function, or other callable object
            name: command name
            description: Text to display in help message
            parse_doc: If True, parse Google style docstring for description.

        Returns:
            None
        """
        if " " in name:
            raise ValueError("name cannot contain spaces; got '%s'" % name)

        # description overrides the function doc string
        if parse_doc and not description:
            parsed = parse_docstr(inspect.getdoc(func))
            description = parsed.summary or parsed.description

        self._parser = None
        self._commands.append((func, name, description))

    def __call__(self, *args):
        """Parse command line arguments, execute callable, and return Result object."""
        # Parse known arguments; remaining arguments are passed to subcommand
        this, extra = self.parser.parse_known_args(args)

        if not this.subcommand:
            self.parser.print_help()
            print("")
            print(_format_epilog(self._commands))
            sys.exit(0)

        # Execute subcommand.
        # If no arguments remain, pass "-h" to prevent parse_args from
        # using sys.argv[1:]. This approach assumes that each tool has
        # at least one required argument.
        subparser = next((item[0] for item in self._commands \
                          if item[1] == this.subcommand), None)

        if extra:
            result = subparser(*extra)
        else:
            result = subparser("-h")

        # If result is not a Result object, assume it is a status code.
        if not isinstance(result, Result):
            result = Result(result, None, None)

        return result
