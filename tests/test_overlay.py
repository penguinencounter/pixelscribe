import typing

import pytest

from pixelscribe import get_justify
from pixelscribe.overlay import Anchor2D, Overlay
from tests.bench import asset_resource_16

verbose = {
    "top left": (Anchor2D.X.LEFT, Anchor2D.Y.TOP),
    "top center": (Anchor2D.X.CENTER, Anchor2D.Y.TOP),
    "top right": (Anchor2D.X.RIGHT, Anchor2D.Y.TOP),
    "center left": (Anchor2D.X.LEFT, Anchor2D.Y.CENTER),
    "center center": (Anchor2D.X.CENTER, Anchor2D.Y.CENTER),
    "center right": (Anchor2D.X.RIGHT, Anchor2D.Y.CENTER),
    "bottom left": (Anchor2D.X.LEFT, Anchor2D.Y.BOTTOM),
    "bottom center": (Anchor2D.X.CENTER, Anchor2D.Y.BOTTOM),
    "bottom right": (Anchor2D.X.RIGHT, Anchor2D.Y.BOTTOM),
    "inside-top right": (Anchor2D.X.RIGHT, Anchor2D.Y.INSIDE_TOP),
    "inside-top left": (Anchor2D.X.LEFT, Anchor2D.Y.INSIDE_TOP),
    "inside-bottom right": (Anchor2D.X.RIGHT, Anchor2D.Y.INSIDE_BOTTOM),
    "inside-bottom left": (Anchor2D.X.LEFT, Anchor2D.Y.INSIDE_BOTTOM),
}
one_word = {
    "center": (Anchor2D.X.CENTER, Anchor2D.Y.CENTER),
    "left": (Anchor2D.X.LEFT, Anchor2D.Y.CENTER),
    "right": (Anchor2D.X.RIGHT, Anchor2D.Y.CENTER),
    "top": (Anchor2D.X.CENTER, Anchor2D.Y.TOP),
    "bottom": (Anchor2D.X.CENTER, Anchor2D.Y.BOTTOM),
}
all_anchors = {**verbose, **one_word}


@pytest.mark.parametrize("anchor,expected", all_anchors.items())
def test_anchor2d_parsing(anchor: str, expected: typing.Tuple[Anchor2D.X, Anchor2D.Y]):
    assert (
        get_justify(anchor, Anchor2D.one_word_aliases, Anchor2D.x_word, Anchor2D.y_word)
        == expected
    )


always_valid = {
    "top left": (Anchor2D.X.LEFT, Anchor2D.Y.TOP),
    "top center": (Anchor2D.X.CENTER, Anchor2D.Y.TOP),
    "top right": (Anchor2D.X.RIGHT, Anchor2D.Y.TOP),
    "center left": (Anchor2D.X.LEFT, Anchor2D.Y.CENTER),
    "center right": (Anchor2D.X.RIGHT, Anchor2D.Y.CENTER),
    "bottom left": (Anchor2D.X.LEFT, Anchor2D.Y.BOTTOM),
    "bottom center": (Anchor2D.X.CENTER, Anchor2D.Y.BOTTOM),
    "bottom right": (Anchor2D.X.RIGHT, Anchor2D.Y.BOTTOM),
}
_edge_and_outside = {
    **always_valid,
    "inside-top right": (Anchor2D.X.RIGHT, Anchor2D.Y.INSIDE_TOP),
    "inside-top left": (Anchor2D.X.LEFT, Anchor2D.Y.INSIDE_TOP),
    "inside-bottom right": (Anchor2D.X.RIGHT, Anchor2D.Y.INSIDE_BOTTOM),
    "inside-bottom left": (Anchor2D.X.LEFT, Anchor2D.Y.INSIDE_BOTTOM),
    "top inside-right": (Anchor2D.X.INSIDE_RIGHT, Anchor2D.Y.TOP),
    "top inside-left": (Anchor2D.X.INSIDE_LEFT, Anchor2D.Y.TOP),
    "bottom inside-right": (Anchor2D.X.INSIDE_RIGHT, Anchor2D.Y.BOTTOM),
    "bottom inside-left": (Anchor2D.X.INSIDE_LEFT, Anchor2D.Y.BOTTOM),
}
modes = {
    Anchor2D.AnchorMode.INSIDE: {
        **always_valid,
        "center center": (Anchor2D.X.CENTER, Anchor2D.Y.CENTER),
    },
    Anchor2D.AnchorMode.EDGE: _edge_and_outside,
    Anchor2D.AnchorMode.OUTSIDE: _edge_and_outside,
}
paired: typing.Dict[
    typing.Tuple[Anchor2D.AnchorMode, str], typing.Tuple[Anchor2D.X, Anchor2D.Y]
] = {}
for mode, anchors in modes.items():
    for anchor, expected in anchors.items():
        paired[(mode, anchor)] = expected


@pytest.mark.parametrize("args,expect", paired.items())
def test_initializer(
    args: typing.Tuple[Anchor2D.AnchorMode, str],
    expect: typing.Tuple[Anchor2D.X, Anchor2D.Y],
):
    assert (
        Overlay(asset_resource_16, anchor_mode=args[0], anchor=args[1]).anchor == expect
    )
