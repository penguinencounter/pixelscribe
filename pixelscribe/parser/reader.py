# https://json.org/json-en.html


import re
import typing

from .json_types import JSONObject


class StringStream:
    def __init__(self, source: str):
        self.source = source
        self.cur = 0

    def read(
        self, count: typing.Optional[int] = None, error_overrun_end: bool = True
    ) -> str:
        if count is None:
            count = len(self.source) - self.cur
        if count + self.cur > len(self.source) and error_overrun_end:
            raise ValueError(
                f"Read overran end of stream (reading {count}, position {self.cur})"
            )
        result = self.source[self.cur : self.cur + count]
        self.cur += count
        return result

    def tell(self) -> int:
        return self.cur

    def peek(self):
        """
        Return the remainder of the stream without moving the cursor
        """
        return self.source[self.cur :]

    def seek(self, to: int):
        if to < 0 or to > len(self.source):
            raise ValueError(f"cannot seek to position {to}")
        self.cur = to


def _take(stream: StringStream, needed_chars: str, error: bool = True) -> bool:
    startpos = stream.tell()
    read = stream.read(len(needed_chars))
    if read != needed_chars and error:
        raise ValueError(
            f"expecting '{needed_chars}', got '{read}' at position {startpos}"
        )
    elif not error:
        # rewind the stream
        stream.seek(startpos)
        return False
    return True


def _whitespace(stream: StringStream):
    regex = r"[ \n\r\t]*"
    number = re.match(regex, stream.peek())
    if number is None:
        raise ValueError("whitespace fail (whaaaaaa?)")
    stream.read(len(number.group(0)))


def loads(json_string: str):
    # WIP
    handle = StringStream(json_string)  # type:ignore


def _json_string(stream: StringStream) -> str:
    _take(stream, '"')
    b = ""
    while True:
        next_c = stream.read(1)
        if next_c == "\\":
            # control characters
            control_char = stream.read(1)
            if control_char == '"':
                b += '"'
            elif control_char == "\\":
                b += "\\"
            elif control_char == "/":
                b += "/"
            elif control_char == "b":
                b += "\b"
            elif control_char == "f":
                b += "\f"
            elif control_char == "n":
                b += "\n"
            elif control_char == "t":
                b += "\t"
            elif control_char == "u":
                hex_digits = stream.read(4)
                if not re.match(r"[0-9a-fA-F]{4}", hex_digits):
                    raise ValueError(
                        f"expecting four hex digits for \\u, got {hex_digits} instead"
                    )
                b += chr(int(hex_digits, 16))
            else:
                raise ValueError(f"unrecognized escape {control_char}")
            continue
        if 0x20 <= ord(next_c) <= 0x10FFF:
            if next_c == '"':
                return b
            b += next_c


def _json_object(stream: StringStream) -> JSONObject:  # todo: migrate types
    _take(stream, "{")
    _whitespace(stream)
    if _take(stream, "}", False):
        return {}
    while True:
        key = _json_string(stream)
        _whitespace(stream)
        _take(stream, ":")
        _whitespace(stream)
        # todo: VALUE
        print(key)
        break
    return {}


if __name__ == "__main__":
    s = StringStream(r'{"among us": true}')
    print(_json_object(s))
    print(s.cur, "...", s.peek())
