# clitool2
Create command line interface for one or more functions.

## Features

* Create a command line interface from a function's parameters.
* Parse the function's docstring to enhance the help message. The docstring must conform to the [Google Python Style Guide](http://google.github.io/styleguide/pyguide.html?showone=Comments#38-comments-and-docstrings).
* Accept list of arguments from a text file prefixed with the '@' character.
* Configure logging and add optional logging parameters to the interface.
* Create a command line interface for multiple functions.

## Installation

### From Source Code

Clone or download the source code, generate wheel file, and install the wheel file using pip.

```bash
python setup.py bdist_wheel
cd dist
python -m pip install --no-index --find-links=. clitool2
```

## Usage

```python
import logging
import sys
from clitool2 import CLITool, CLIToolbox

def greet(name):
    """Greet person.

    Args:
        name: name of person

    Returns:
        None
    """
    logging.info("Hello %s", name)

tool = CLITool(greet, parse_doc=True)

# The help message includes information from the greet docstring.
# It also shows the additional logging parameters.
tool("-h")
# usage: usage.py [-h] [--logfile LOGFILE] [--logwrite LOGWRITE]
#               [--loglevel LOGLEVEL]
#               name
#
# Greet person.
#
# positional arguments:
#   name                 name of person
#
# optional arguments:
#   -h, --help           show this help message and exit
#
# logging arguments:
#   --logfile LOGFILE    log file name; file is opened in append mode.
#   --logwrite LOGWRITE  log file name; file is opened in write mode.
#   --loglevel LOGLEVEL  logging level; default is 20 (logging.INFO).

# CLITool adds a start and end log message.
tool("Bob")
# [INFO] Start Time: 2020-04-21 14:31:59
# [INFO] Hello Bob
# [INFO] SUCCEEDED at 2020-04-21 14:31:59 (Elapsed Time: 0:00:00.00)

# CLIToolbox can create a command line interface for one or more CLITool objects.
toolbox = CLIToolbox()
toolbox.add_command(tool, "greet", "Greet person")

toolbox("-h")
# usage: usage.py [{greet}]
#
# positional arguments:
#   {greet}
#
# Commands:
#   greet           Greet person

toolbox("greet", "Frank")
# [INFO] Start Time: 2020-04-21 14:35:02
# [INFO] Hello Frank
# [INFO] SUCCEEDED at 2020-04-21 14:35:02 (Elapsed Time: 0:00:00.00)
```

## Running the tests

```python
python -m tests
```

## License
[MIT](https://choosealicense.com/licenses/mit/)