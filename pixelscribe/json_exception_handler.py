import os.path
import typing

from pixelscribe import JSONTraceable, exceptions
from pixelscribe.parser.reader import FilePosStorage


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
        for i in range(line_col[0] - 2, line_col[0] + 3):
            if 0 < i <= len(lines):
                result += f"{str(i).rjust(lineno_width)}: {lines[i-1]}\n"
    # ...
    return result
