# https://json.org/json-en.html


import re
import typing
from pprint import pprint as rp

from .json_types import JSON, JSONArray, JSONObject

# from json_types import JSON, JSONArray, JSONObject


JsonPath = typing.List[typing.Union[str, int]]
FrozenJsonPath = typing.Tuple[typing.Union[str, int], ...]


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

    def rewind(self, by: int):
        self.seek(self.cur - by)

    def eof(self):
        return self.cur >= len(self.source)


class FilePosStorage:
    def __init__(self):
        self.positions: typing.Dict[FrozenJsonPath, int] = {}

    def put(self, path_to: JsonPath, position: int, allow_overwrite: bool = False):
        # freeze
        fzn: FrozenJsonPath = tuple(path_to)
        if fzn in self.positions and not allow_overwrite:
            raise KeyError("Path already assigned a file position")
        self.positions[fzn] = position


def _take(stream: StringStream, needed_chars: str, error: bool = True) -> bool:
    startpos = stream.tell()
    read = stream.read(len(needed_chars), error)
    if read != needed_chars:
        if error:
            raise ValueError(
                f"expecting '{needed_chars}', got '{read}' at position {startpos}\n "
                f"stream={stream.source[startpos:startpos+32]}"
            )
        else:
            # rewind the stream
            stream.seek(startpos)
            return False
    return True


def _check(stream: StringStream, checked_chars: str) -> bool:
    startpos = stream.tell()
    read = stream.read(len(checked_chars))
    stream.seek(startpos)  # rewind the stream
    return read == checked_chars


def _whitespace(stream: StringStream):
    if stream.eof():
        return
    regex = r"[ \n\r\t]*"
    number = re.match(regex, stream.peek())
    if number is None:
        raise ValueError("whitespace fail (whaaaaaa?)")
    stream.read(len(number.group(0)))


def loads(json_string: str) -> typing.Tuple[JSON, FilePosStorage]:
    # WIP
    handle = StringStream(json_string)  # type:ignore
    store = FilePosStorage()
    return _json_value(handle, store), store


def _json_value(
    stream: StringStream,
    path_storage: FilePosStorage,
    path_to_this: typing.Optional[JsonPath] = None,
) -> JSON:
    if path_to_this is None:
        path_to_this = []
    path_storage.put(path_to_this, stream.tell())
    _whitespace(stream)
    res: JSON
    # Simple stuff
    if _take(stream, "true", False):
        res = True
    elif _take(stream, "false", False):
        res = False
    elif _take(stream, "null", False):
        res = None
    elif _check(stream, '"'):
        res = _json_string(stream)
    # Complicated stuff
    elif _check(stream, "{"):
        res = _json_object(stream, path_storage, path_to_this)
    elif _check(stream, "["):
        res = _json_array(stream, path_storage, path_to_this)
    else:
        # is it a NUMBER?
        next_char = stream.peek()[0]  # next char, no advance
        if next_char in "-0123456789":
            # yeah ok
            res = _json_number(stream)
        else:
            # no clue lol
            raise ValueError(
                f"expecting JSON value at position {stream.tell()} ({stream.peek()[:16]})"
            )
    _whitespace(stream)
    return res


def _json_number(stream: StringStream) -> typing.Union[float, int]:
    # it can have a negative sign
    is_negative = _take(stream, "-", False)

    # Main digit part
    def digits() -> int:
        digits = 0
        if _take(stream, "0", False):
            return digits
        next_c = stream.read(1)
        if next_c not in "123456789":
            raise ValueError(
                f"numbers other than 0 must start with 1-9, not '{next_c}'\n{stream.peek()[:32]}"
            )
        digits += int(next_c)
        while True:
            next_c = stream.read(1, False)
            if next_c == "":
                # end of stream
                break
            if next_c not in "0123456789":
                stream.rewind(1)
                break
            digits *= 10
            digits += int(next_c)
        return digits

    d = digits()

    def fraction() -> float:
        if stream.eof():
            return 0.0
        if not _take(stream, ".", False):
            return 0.0
        fraction = 0.0
        invexp = -1
        # read digits
        while True:
            next_c = stream.read(1, False)
            if next_c == "":
                # end of stream
                break
            if next_c not in "0123456789":
                stream.rewind(1)
                break
            fraction += float(next_c) * (10.0**invexp)
            invexp -= 1
        return fraction

    f = fraction()

    def exponent() -> int:
        if stream.eof():
            return 0
        if not (_take(stream, "e", False) or _take(stream, "E", False)):
            return 0
        exponent = 0
        exponent_negative = _take(stream, "-", False)
        if not exponent_negative:
            _take(stream, "+", False)  # optionally have a plus sign
        # read digits
        while True:
            next_c = stream.read(1, False)
            if next_c == "":
                # end of stream
                break
            if next_c not in "0123456789":
                stream.rewind(1)
                break
            exponent *= 10
            exponent += int(next_c)
        if exponent_negative:
            exponent *= -1
        return exponent

    e = exponent()

    # put it all together
    result = (d + f) * (10**e)
    if is_negative:
        result *= -1
    if int(result) == result:
        return int(result)
    return result


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


def _json_object(
    stream: StringStream, path_storage: FilePosStorage, path_to_this: JsonPath
) -> JSONObject:  # todo: migrate types
    _take(stream, "{")
    _whitespace(stream)
    if _take(stream, "}", False):
        return {}
    result: JSONObject = {}
    while True:
        key = _json_string(stream)
        _whitespace(stream)
        _take(stream, ":")
        _whitespace(stream)
        value = _json_value(
            stream, path_storage=path_storage, path_to_this=path_to_this + [key]
        )
        _whitespace(stream)
        # , or }
        result[key] = value
        if _take(stream, "}", False):
            break
        _take(stream, ",")
        _whitespace(stream)
    return result


def _json_array(
    stream: StringStream, path_storage: FilePosStorage, path_to_this: JsonPath
) -> JSONArray:
    _take(stream, "[")
    _whitespace(stream)
    if _take(stream, "]", False):
        return []
    result: JSONArray = []
    index = 0
    while True:
        _whitespace(stream)
        value = _json_value(
            stream, path_storage=path_storage, path_to_this=path_to_this + [index]
        )
        result.append(value)
        _whitespace(stream)
        index += 1
        if _take(stream, "]", False):
            break
        _take(stream, ",")
        _whitespace(stream)
    return result


if __name__ == "__main__":
    with open("/workspaces/pixelscribe/pixelscribe/theme-schema.json") as f:
        s = f.read()
    result, store = loads(s)
    print(result)
    rp(store.positions)
