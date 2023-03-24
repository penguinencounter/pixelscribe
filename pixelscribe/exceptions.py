import typing
from enum import Enum
from typing import Tuple, Union


def line_col(source: str, index: int) -> Tuple[int, int]:
    """
    Return the line and column number of the given index in the source string.
    """
    return source.count("\n", 0, index) + 1, index - source.rfind("\n", 0, index)


class JSONTraceable(Exception):
    """
    Base class for exceptions that can be traced back to JSON.
    """

    def __init__(
        self,
        message: str,
        json_path: typing.Union[str, typing.List[typing.Union[str, int]]] = "",
    ):
        super().__init__(message)
        self.json_path: typing.List[typing.Union[str, int]]
        if isinstance(json_path, str):
            if json_path == "":
                self.json_path = []
            else:
                self.json_path = [json_path]
        elif isinstance(json_path, list):  # type: ignore[reportUnnecessaryIsInstance]
            self.json_path = json_path
        else:
            raise TypeError(
                f"JSON path should be a string or a list, not {type(json_path).__name__}"
            )
        self.source_file: typing.Optional[str] = None

    def extend(self, key: typing.Union[str, int]):
        self.json_path.insert(0, key)

    def set_source_file(self, source_file: str):
        self.source_file = source_file


class ValidationError(JSONTraceable):
    class ErrorCode(Enum):
        MISSING_VALUE = 1
        WRONG_TYPE = 2
        INVALID_VALUE = 3

    def __init__(
        self,
        message: str,
        error_code: Union[int, ErrorCode] = -1,
        json_path: typing.Union[str, typing.List[typing.Union[str, int]]] = "",
    ):
        if isinstance(error_code, ValidationError.ErrorCode):
            error_code = error_code.value
        super().__init__(
            "[code {} ({})] {}".format(
                error_code,
                ValidationError.ErrorCode(error_code).name
                if error_code in [x.value for x in ValidationError.ErrorCode]
                else "unknown",
                message,
            ),
            json_path,
        )
        self.error_code = error_code
