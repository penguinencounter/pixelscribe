import random
from typing import Dict

import pytest
from PIL import Image

from pixelscribe.asset_resource import (AssetResource, Direction, Feature1D,
                                        Justify1D)

all_anchors = {
    "start": Justify1D.START,
    "center": Justify1D.CENTER,
    "end": Justify1D.END,
    "left": Justify1D.START,
    "right": Justify1D.END,
    "top": Justify1D.START,
    "bottom": Justify1D.END,
}
i16h = Image.new("RGBA", (4, 16), (255, 0, 0, 0))
i16h.paste(Image.new("RGBA", (2, 14), (0, 0, 0, 128)), (1, 1))
asset_16 = AssetResource.from_image(i16h)
i16v = Image.new("RGBA", (16, 4), (255, 0, 0, 0))
i16v.paste(Image.new("RGBA", (14, 2), (0, 0, 0, 128)), (1, 1))

i16 = {
    Direction.HORIZONTAL: i16h,
    Direction.VERTICAL: i16v,
}

i13h = Image.new("RGBA", (3, 13), (255, 0, 0, 0))
i13h.paste(Image.new("RGBA", (1, 11), (0, 0, 0, 128)), (1, 1))
i13v = Image.new("RGBA", (13, 3), (255, 0, 0, 0))
i13v.paste(Image.new("RGBA", (11, 1), (0, 0, 0, 128)), (1, 1))

i13 = {
    Direction.HORIZONTAL: i13h,
    Direction.VERTICAL: i13v,
}


@pytest.mark.parametrize("anchor,expected", all_anchors.items())
def test_anchor_parsing(anchor: str, expected: Justify1D):
    assert Justify1D.from_name(anchor) == expected


@pytest.mark.parametrize("anchor,expected", all_anchors.items())
def test_initializer(anchor: str, expected: Justify1D):
    assert Feature1D(asset_16, anchor).justify == expected


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
