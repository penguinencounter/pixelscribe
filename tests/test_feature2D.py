import typing

import pytest

from pixelscribe.asset_resource import AssetResource, get_justify
from pixelscribe.feature_2d import Feature2D, Justify2D
from tests.bench import (
    asset_resource_13,
    asset_resource_16,
    override_2d_13,
    override_2d_16,
)

verbose = {
    "top left": (Justify2D.X.LEFT, Justify2D.Y.TOP),
    "top center": (Justify2D.X.CENTER, Justify2D.Y.TOP),
    "top right": (Justify2D.X.RIGHT, Justify2D.Y.TOP),
    "center left": (Justify2D.X.LEFT, Justify2D.Y.CENTER),
    "center center": (Justify2D.X.CENTER, Justify2D.Y.CENTER),
    "center right": (Justify2D.X.RIGHT, Justify2D.Y.CENTER),
    "bottom left": (Justify2D.X.LEFT, Justify2D.Y.BOTTOM),
    "bottom center": (Justify2D.X.CENTER, Justify2D.Y.BOTTOM),
    "bottom right": (Justify2D.X.RIGHT, Justify2D.Y.BOTTOM),
}
one_word = {
    "center": (Justify2D.X.CENTER, Justify2D.Y.CENTER),
    "left": (Justify2D.X.LEFT, Justify2D.Y.CENTER),
    "right": (Justify2D.X.RIGHT, Justify2D.Y.CENTER),
    "top": (Justify2D.X.CENTER, Justify2D.Y.TOP),
    "bottom": (Justify2D.X.CENTER, Justify2D.Y.BOTTOM),
}
all_anchors = {**verbose, **one_word}

tiling_test_sizes = {
    "even1": asset_resource_16,
    "odd1": asset_resource_13,
}


@pytest.mark.parametrize("anchor,expected", all_anchors.items())
def test_anchor_parsing(anchor: str, expected: typing.Tuple[Justify2D.X, Justify2D.Y]):
    assert (
        get_justify(
            anchor, Justify2D.one_word_aliases, Justify2D.x_word, Justify2D.y_word
        )
        == expected
    )


@pytest.mark.parametrize("anchor,expected", all_anchors.items())
def test_initializer(anchor: str, expected: typing.Tuple[Justify2D.X, Justify2D.Y]):
    assert Feature2D(asset_resource_16, anchor).justify == expected


def test_compatible_override():
    Feature2D(asset_resource_16, "top left", [override_2d_16])


def test_incompatible_override():
    with pytest.raises(ValueError) as exec_info:
        Feature2D(asset_resource_16, "top left", [override_2d_13])
    print("\nexception message:\n", exec_info.value.args[0])


@pytest.mark.parametrize("anchor", all_anchors.keys())
@pytest.mark.parametrize("image", tiling_test_sizes.values())
@pytest.mark.parametrize("size", [(20, 20), (19, 19), (20, 19), (19, 20)])
def test_tiling(image: AssetResource, anchor: str, size: typing.Tuple[int, int]):
    f = Feature2D(image, anchor)
    t = f.tile(*size)
    assert t.size == size
