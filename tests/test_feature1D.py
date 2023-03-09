import random
from typing import Dict

import pytest
from PIL import Image

from pixelscribe.asset_resource import AssetResource
from pixelscribe.feature_1d import Direction, Feature1D, Justify1D
from tests.bench import asset_resource_horizontal_16, i13h, i13v, i16h, i16v

all_anchors = {
    "start": Justify1D.START,
    "center": Justify1D.CENTER,
    "end": Justify1D.END,
    "left": Justify1D.START,
    "right": Justify1D.END,
    "top": Justify1D.START,
    "bottom": Justify1D.END,
}

i16 = {
    Direction.HORIZONTAL: i16h,
    Direction.VERTICAL: i16v,
}


i13 = {
    Direction.HORIZONTAL: i13h,
    Direction.VERTICAL: i13v,
}


@pytest.mark.parametrize("anchor,expected", all_anchors.items())
def test_anchor_parsing(anchor: str, expected: Justify1D):
    assert Justify1D.from_name(anchor) == expected


@pytest.mark.parametrize("anchor,expected", all_anchors.items())
def test_initializer(anchor: str, expected: Justify1D):
    assert Feature1D(asset_resource_horizontal_16, anchor).justify == expected


def rng_even_size() -> int:
    return random.randint(4, 64) * 2


def rng_odd_size() -> int:
    return rng_even_size() + 1


@pytest.mark.parametrize("anchor", all_anchors.keys())
@pytest.mark.parametrize("direction", [Direction.HORIZONTAL, Direction.VERTICAL])
@pytest.mark.parametrize("pool", [i16, i13])
@pytest.mark.parametrize("size", [20, 19])
def test_rendering(
    anchor: str, direction: Direction, pool: Dict[Direction, Image.Image], size: int
):
    feature = Feature1D(AssetResource.from_image(pool[direction]), anchor, direction)
    image = feature.tile(size)
    if direction == Direction.HORIZONTAL:
        assert image.width == size
        assert image.height == pool[direction].height
    else:
        assert image.width == pool[direction].width
        assert image.height == size
