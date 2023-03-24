import typing
from typing import Union

from pixelscribe import JSONTraceable


class JsonContext(object):
    def __init__(self, *key_or_index: Union[str, int]):
        """
        @param key_or_index: A list of keys and/or indices to be used to trace the JSON path.
                Keys are applied in the reverse order, so the first key is the shallowest.
        """
        self.key_or_index = key_or_index

    def __enter__(self):
        return None

    def __exit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_val: typing.Optional[BaseException],
        exc_tb: typing.Any,
    ):
        if exc_type is None:
            return
        if issubclass(exc_type, JSONTraceable):
            exc_val = typing.cast(JSONTraceable, exc_val)
            for key in reversed(self.key_or_index):
                exc_val.extend(key)
        return False


class JsonFileContext(object):
    def __init__(self, source_file: str):
        self.source_file = source_file

    def __enter__(self):
        return None

    def __exit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_val: typing.Optional[BaseException],
        exc_tb: typing.Any,
    ):
        if exc_type is None:
            return
        if issubclass(exc_type, JSONTraceable):
            exc_val = typing.cast(JSONTraceable, exc_val)
            exc_val.set_source_file(self.source_file)
        return False
