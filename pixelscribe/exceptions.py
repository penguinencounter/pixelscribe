from enum import Enum
from typing import Union


class JSONTraceable(Exception):
    """
    Base class for exceptions that can be traced back to JSON.
    """

    def __init__(self, message: str, json_path: str = ""):
        super().__init__(message)
        self.json_path = json_path

    def extend_parent_key(self, key: str):
        self.json_path = f".{key}{self.json_path}"

    def extend_parent_index(self, index: int):
        self.json_path = f"[{index}]{self.json_path}"


class ValidationError(JSONTraceable):
    class ErrorCode(Enum):
        MISSING_VALUE = 1
        WRONG_TYPE = 2
        INVALID_VALUE = 3

    def __init__(
        self, message: str, error_code: Union[int, ErrorCode] = -1, json_path: str = ""
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
