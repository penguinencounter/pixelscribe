import os.path
import typing

from pixelscribe import JSONTraceable, exceptions
from pixelscribe.parser.reader import FilePosStorage


def handle(exception: JSONTraceable, import_data: typing.Optional[FilePosStorage]):
    print(exception.args[0])  # message
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

    error_locator_header_line = (
        f'  at {".".join(map(str, exception.json_path))}' f' in "{nice_filename}"'
    )
    if source:
        error_locator_header_line += f", line {line_col[0]} (column {line_col[1]})"
    print(error_locator_header_line)
    # if the file exists, try to start reading it...
