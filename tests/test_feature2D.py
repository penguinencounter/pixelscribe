import typing

import pytest
from PIL import Image

from pixelscribe.asset_resource import (
    AssetResource,
    Feature2D,
    Feature2DOverride,
    Justify2D,
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

i16 = Image.new("RGBA", (16, 16), (255, 0, 0, 255))
i16.paste(Image.new("RGBA", (14, 14), (0, 0, 0, 128)), (1, 1))
i16_2 = Image.new("RGBA", (16, 16), (255, 255, 0, 255))
i16_2.paste(Image.new("RGBA", (14, 14), (0, 0, 0, 128)), (1, 1))
dummy_image_16 = AssetResource.from_image(i16)
dummy_image_16_2 = AssetResource.from_image(i16_2)

i32 = Image.new("RGBA", (32, 32), (0, 255, 0, 255))
i32.alpha_composite(Image.new("RGBA", (30, 30), (0, 0, 0, 128)), (1, 1))
dummy_image_32 = AssetResource.from_image(i32)

i13 = Image.new("RGBA", (13, 13), (0, 0, 255, 255))
i13.alpha_composite(Image.new("RGBA", (11, 11), (0, 0, 0, 128)), (1, 1))
dummy_image_13 = AssetResource.from_image(i13)

tiling_test_sizes = {
    "even1": dummy_image_16,
    "odd1": dummy_image_13,
}

override_16 = Feature2DOverride(dummy_image_16_2, 0, 0)
override_13 = Feature2DOverride(dummy_image_13, 0, 0)
override_32 = Feature2DOverride(dummy_image_32, 0, 0)


@pytest.mark.parametrize("anchor,expected", all_anchors.items())
def test_anchor_parsing(anchor: str, expected: typing.Tuple[Justify2D.X, Justify2D.Y]):
    assert Feature2D.get_justify(anchor) == expected


@pytest.mark.parametrize("anchor,expected", all_anchors.items())
def test_initializer(anchor: str, expected: typing.Tuple[Justify2D.X, Justify2D.Y]):
    assert Feature2D(dummy_image_16, anchor).justify == expected


def test_compatible_override():
    Feature2D(dummy_image_16, "top left", [override_16])


def test_incompatible_override():
    with pytest.raises(ValueError) as exec_info:
        Feature2D(dummy_image_16, "top left", [override_13])
    print("\nexception message:\n", exec_info.value.args[0])


@pytest.mark.parametrize("anchor", all_anchors.keys())
@pytest.mark.parametrize("image", tiling_test_sizes.values())
@pytest.mark.parametrize("size", [(20, 20), (19, 19), (20, 19), (19, 20)])
def test_even_tile_size(
    image: AssetResource, anchor: str, size: typing.Tuple[int, int]
):
    f = Feature2D(image, anchor)
    t = f.tile(*size)
    assert t.size == size
