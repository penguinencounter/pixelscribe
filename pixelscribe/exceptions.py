from enum import Enum
from typing import Union


class ValidationError(ValueError):
    class ErrorCode(Enum):
        MISSING_VALUE = 1
        WRONG_TYPE = 2
        INVALID_VALUE = 3

    def __init__(self, message: str, error_code: Union[int, ErrorCode] = -1):
        if isinstance(error_code, ValidationError.ErrorCode):
            error_code = error_code.value
        super().__init__(
            "[code {} ({})] {}".format(
                error_code,
                ValidationError.ErrorCode(error_code).name
                if error_code in [x.value for x in ValidationError.ErrorCode]
                else "unknown",
                message,
            )
        )
        self.error_code = error_code
