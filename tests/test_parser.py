import json
import random
import string
import typing

import pytest

from pixelscribe import JSON
from pixelscribe.parser import loads


def test_list():
    assert loads("[]")[0] == []


def test_dict():
    assert loads("{}")[0] == {}


def test_string():
    assert loads('"foo"')[0] == "foo"


def test_number():
    assert loads("42")[0] == 42


def test_other():
    assert loads("true")[0] is True
    assert loads("false")[0] is False
    assert loads("null")[0] is None


def generate_fuzzing_data(max_branch: int = 10) -> typing.Tuple[str, JSON]:
    def random_str():
        return "".join(random.choices(string.ascii_letters, k=random.randint(1, 50)))

    def random_int():
        return random.randint(-100, 100)

    def random_float():
        r = round(random.random() * 100, 4)
        if r.is_integer():
            return int(r)
        return r

    def random_special():
        return random.choice([True, False, None])

    def random_list():
        return [
            generate_fuzzing_data(max_branch // 4 * 3)[1]
            for _ in range(random.randint(0, max_branch))
        ]

    def random_dict():
        return {
            random_str(): generate_fuzzing_data(max_branch // 4 * 3)[1]
            for _ in range(random.randint(0, max_branch))
        }

    def random_value():
        return random.choice(
            [
                random_str,
                random_int,
                random_float,
                random_special,
                random_list,
                random_dict,
            ]
        )()

    v = random_value()
    return json.dumps(v), v


@pytest.mark.parametrize("iteration", range(1, 100))
def test_auto_generate(iteration: int):
    head = f"\rtest i={iteration}"
    data_s, data_t = generate_fuzzing_data(20)
    print(head, "Generating test data", end="", flush=True)
    print(head, end="\n", flush=True)
    print("fuz: ", data_s)

    def compare(a: typing.Any, b: typing.Any) -> bool:
        OK_ERROR = 1e-6
        if type(a) != type(b):
            return False
        if isinstance(a, dict):
            a = typing.cast(typing.Dict[typing.Any, typing.Any], a)
            b = typing.cast(typing.Dict[typing.Any, typing.Any], b)
            return all(compare(a[k], b[k]) for k in a)
        if isinstance(a, list):
            a = typing.cast(typing.List[typing.Any], a)
            b = typing.cast(typing.List[typing.Any], b)
            return all(compare(a[i], b[i]) for i in range(len(a)))
        if isinstance(a, float):
            b = typing.cast(float, b)
            return abs(a - b) < OK_ERROR
        return a == b

    if not compare(loads(data_s)[0], data_t):
        print("want: ", data_t)
        print("have: ", loads(data_s)[0])
        assert False
