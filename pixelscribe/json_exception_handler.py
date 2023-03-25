import os.path
import typing

# pycharm bug
# noinspection PyUnresolvedReferences
from colorama import Fore, Style, just_fix_windows_console

from pixelscribe import JSONTraceable, exceptions
from pixelscribe.parser.reader import FilePosStorage

just_fix_windows_console()


CONTEXT = 5


def handle(exception: JSONTraceable, import_data: typing.Optional[FilePosStorage]):
    result = ""
    result += exception.args[0] + "\n"  # message
    nice_filename = "<unknown>"
    source = None
    line_col = (0, 0)
    if exception.source_file:
        if os.path.exists(exception.source_file):
            nice_filename = os.path.abspath(exception.source_file)
            if import_data:
                with open(nice_filename) as f:
                    source = f.read()
                line_col = exceptions.line_col(
                    source, import_data.get(exception.json_path)
                )

    nice_error_path = (
        ".".join(map(str, exception.json_path))
        if len(exception.json_path) > 0
        else "<root object>"
    )
    error_locator_header_line = f"  at {nice_error_path}" f' in "{nice_filename}"'
    if source:
        error_locator_header_line += f", line {line_col[0]} (column {line_col[1]})"
    result += error_locator_header_line + "\n"
    # if the file exists, try to start reading it...
    if source:
        # read by lines
        lines = source.splitlines()
        lineno_width = len(str(line_col[0])) + 1
        # print two lines before the error
        for i in range(line_col[0] - CONTEXT, line_col[0] + CONTEXT + 1):
            linebar = " \u2502"
            if i == line_col[0] - CONTEXT or i == 1:
                if i != 1:
                    linebar = " ↑"
                else:
                    linebar = " \u2577"
            if i == line_col[0] + CONTEXT or i == len(lines):
                if i != len(lines):
                    linebar = " ↓"
                else:
                    linebar = " \u2575"
            if i == line_col[0]:
                linebar = "->"
            if 0 < i <= len(lines):
                if i == line_col[0]:
                    result += (
                        f"{Fore.YELLOW}{Style.BRIGHT}{str(i).rjust(lineno_width)}{linebar}"
                        f"{lines[i-1]}{Style.RESET_ALL}\n"
                    )
                else:
                    result += f"{str(i).rjust(lineno_width)}{linebar} {lines[i-1]}\n"
    # ...
    return result
