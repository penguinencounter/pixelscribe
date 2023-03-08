import enum
import typing
from typing import Union

from PIL import Image

from pixelscribe import (
    JSON,
    AssetResource,
    Feature,
    FeatureOverride,
    ValidationError,
    check_feature,
    get_justify,
    next_multiple,
    odd,
)


class Justify2D:
    @enum.unique
    class X(enum.Enum):
        LEFT = "left"
        CENTER = "center"
        RIGHT = "right"

        def __repr__(self):
            return f"{self.value}"

    @enum.unique
    class Y(enum.Enum):
        TOP = "top"
        CENTER = "center"
        BOTTOM = "bottom"

        def __repr__(self):
            return f"{self.value}"

    one_word_aliases = {
        "center": ("center", "center"),
        "left": ("center", "left"),
        "right": ("center", "right"),
        "top": ("top", "center"),
        "bottom": ("bottom", "center"),
    }

    x_word = {"left": X.LEFT, "center": X.CENTER, "right": X.RIGHT}

    y_word = {"top": Y.TOP, "center": Y.CENTER, "bottom": Y.BOTTOM}


class Feature2DOverride(FeatureOverride):
    def __init__(self, asset: AssetResource, x: int, y: int):
        super().__init__(asset)
        self.x = x
        self.y = y

    @classmethod
    def import_(cls, json_body: JSON, theme_directory: typing.Optional[str] = None):
        if not isinstance(json_body, dict):
            raise ValidationError(
                f"JSON body for FeatureOverride should be a dict, not {json_body.__class__.__name__}",
                ValidationError.ErrorCode.WRONG_TYPE,
            )
        asset = AssetResource.import_(json_body, theme_directory)
        if "index" not in json_body:
            raise ValidationError(
                'FeatureOverride(s) require a "index".',
                ValidationError.ErrorCode.MISSING_VALUE,
            )
        index = json_body["index"]
        if not isinstance(index, list):
            raise ValidationError(
                f"FeatureOverride index should be a list, not {index.__class__.__name__}",
                ValidationError.ErrorCode.WRONG_TYPE,
            )
        if len(index) != 2:
            raise ValidationError(
                f"FeatureOverride index should be a list of length 2, not length {len(index)}",
                ValidationError.ErrorCode.WRONG_TYPE,
            )
        if not all(
            isinstance(i, int) or (isinstance(i, float) and i.is_integer())
            for i in index
        ):
            raise ValidationError(
                f"FeatureOverride index should be a list of ints. (provided: {index})",
                ValidationError.ErrorCode.WRONG_TYPE,
            )
        index = typing.cast(typing.List[Union[int, float]], index)
        return cls(asset, int(index[0]), int(index[1]))


class Feature2D(Feature):
    FEATURE_TYPES = ["background", "code_background"]

    def __init__(
        self,
        asset: AssetResource,
        justify: typing.Union[str, typing.Tuple[Justify2D.X, Justify2D.Y]] = "center",
        overrides: typing.Optional[typing.List[Feature2DOverride]] = None,
    ):
        super().__init__(asset)
        self._overrides = {}
        self.set_overrides(overrides)
        if isinstance(justify, str):
            justify = get_justify(
                justify, Justify2D.one_word_aliases, Justify2D.x_word, Justify2D.y_word
            )
        self.justifyX, self.justifyY = justify

    def set_overrides(self, overrides: typing.Optional[typing.List[Feature2DOverride]]):
        self._overrides: typing.Dict[typing.Tuple[int, int], Feature2DOverride] = {
            (o.x, o.y): o for o in (overrides or [])
        }
        for override in self._overrides.values():
            if override.asset.get().size != self._asset.get().size:
                raise ValueError(
                    "Override asset size must match the base asset size.\n    "
                    f"got {override.asset.get().size}, expected {self._asset.get().size}\n    "
                    "(hint: try resizing the override with the 'crop' option)\n    "
                    "(hint: if you don't want to do that, use an overlay instead)"
                )

    @property
    def justify(self) -> typing.Tuple[Justify2D.X, Justify2D.Y]:
        return self.justifyX, self.justifyY

    def tile(self, width: int, height: int):
        """
        Tile the asset to the given dimensions.
        :param width: The width to tile to.
        :param height: The height to tile to.
        :return: The tiled image.
        """
        img = self._asset.get()
        # Round up to the next multiple of the asset size...
        tiled = Image.new(
            "RGBA",
            (
                odd(next_multiple(width, img.width)),
                odd(next_multiple(height, img.height)),
            ),
        )
        tile_count = tiled.width // img.width, tiled.height // img.height
        # Calculate the "origin" tile
        center_pos = [0, 0]
        if self.justifyX == Justify2D.X.CENTER:
            center_pos[0] = tile_count[0] // 2
        elif self.justifyX == Justify2D.X.RIGHT:
            center_pos[0] = tile_count[0] - 1
        if self.justifyY == Justify2D.Y.CENTER:
            center_pos[1] = tile_count[1] // 2
        elif self.justifyY == Justify2D.Y.BOTTOM:
            center_pos[1] = tile_count[1] - 1

        # Paste that thing all over the place
        for x in range(tile_count[0]):
            for y in range(tile_count[1]):
                vx, vy = x - center_pos[0], y - center_pos[1]
                if (vx, vy) in self._overrides:
                    override = self._overrides[(vx, vy)]
                    tiled.paste(override.asset.get(), (x * img.width, y * img.height))
                else:
                    tiled.paste(img, (x * img.width, y * img.height))

        # Crop to the desired size using the justification
        crop_from = [0, 0]
        if self.justifyX == Justify2D.X.CENTER:
            crop_from[0] = (tiled.width - width) // 2
        elif self.justifyX == Justify2D.X.RIGHT:
            crop_from[0] = tiled.width - width
        if self.justifyY == Justify2D.Y.CENTER:
            crop_from[1] = (tiled.height - height) // 2
        elif self.justifyY == Justify2D.Y.BOTTOM:
            crop_from[1] = tiled.height - height
        crop_to = [crop_from[0] + width, crop_from[1] + height]
        tiled = tiled.crop((crop_from[0], crop_from[1], crop_to[0], crop_to[1]))
        return tiled

    @classmethod
    def import_(cls, json_body: JSON, theme_directory: typing.Optional[str] = None):
        if not isinstance(json_body, dict):
            raise ValidationError(
                f"JSON body for Feature should be a dict, not {json_body.__class__.__name__}",
                ValidationError.ErrorCode.WRONG_TYPE,
            )
        asset = AssetResource.import_(json_body, theme_directory)
        justify = json_body.get("justify", "top left")
        if not isinstance(justify, str):
            raise ValidationError(
                f"JSON body for Feature justify should be a string, not {justify.__class__.__name__}",
                ValidationError.ErrorCode.WRONG_TYPE,
            )
        overrides = json_body.get("overrides", [])
        if not isinstance(overrides, list):
            raise ValidationError(
                f"JSON body for Feature overrides should be a list, not {overrides.__class__.__name__}",
                ValidationError.ErrorCode.WRONG_TYPE,
            )

        # might throw, OK
        overrides = [Feature2DOverride.import_(o, theme_directory) for o in overrides]

        check_feature(json_body, cls.FEATURE_TYPES)

        return cls(asset, justify, overrides)
