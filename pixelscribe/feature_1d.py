import enum
import typing

from PIL import Image

from pixelscribe import (
    JSON,
    AssetResource,
    Feature,
    FeatureOverride,
    JSONTraceable,
    ValidationError,
    check_feature,
    next_multiple,
    odd,
)


@enum.unique
class Justify1D(enum.Enum):
    START = "start"
    CENTER = "center"
    END = "end"

    @classmethod
    def from_name(cls, name: str) -> "Justify1D":
        m = {
            "start": cls.START,
            "center": cls.CENTER,
            "end": cls.END,
            "left": cls.START,
            "right": cls.END,
            "top": cls.START,
            "bottom": cls.END,
        }
        if name.lower() not in m:
            raise ValidationError(
                f"Invalid justify code: {name.lower()} is not supported",
                ValidationError.ErrorCode.INVALID_VALUE,
            )
        return m[name.lower()]


@enum.unique
class Direction(enum.Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"

    @classmethod
    def from_name(cls, name: str) -> "Direction":
        return {"horizontal": cls.HORIZONTAL, "vertical": cls.VERTICAL}[name.lower()]


class Feature1DOverride(FeatureOverride):
    def __init__(self, asset: AssetResource, x: int):
        super().__init__(asset)
        self.x = x

    @classmethod
    def import_(cls, json_body: JSON, theme_directory: typing.Optional[str] = None):
        if not isinstance(json_body, dict):
            raise ValidationError(
                f"JSON body for FeatureOverride should be a dict, not {json_body.__class__.__name__}",
                ValidationError.ErrorCode.WRONG_TYPE,
                "",
            )
        asset = AssetResource.import_(json_body, theme_directory)
        if "index" not in json_body:
            raise ValidationError(
                'FeatureOverride(s) require a "index".',
                ValidationError.ErrorCode.MISSING_VALUE,
                "",
            )
        index = json_body["index"]
        if not (
            isinstance(index, int) or (isinstance(index, float) and index.is_integer())
        ):
            raise ValidationError(
                f"FeatureOverride index should be an integer. (provided: {index})",
                ValidationError.ErrorCode.WRONG_TYPE,
                ".index",
            )
        index = typing.cast(typing.Union[int, float], index)
        return cls(asset, int(index))


class Feature1D(Feature):
    FEATURE_TYPES = [
        "top_edge",
        "bottom_edge",
        "left_edge",
        "right_edge",
        "block_quote",
        "code_top_edge",
        "code_bottom_edge",
        "code_left_edge",
        "code_right_edge",
        "horizontal_rule",
    ]
    HORIZONTAL_TYPES = [
        "top_edge",
        "bottom_edge",
        "code_top_edge",
        "code_bottom_edge",
        "horizontal_rule",
    ]
    VERTICAL_TYPES = [
        "left_edge",
        "right_edge",
        "block_quote",
        "code_left_edge",
        "code_right_edge",
    ]

    @staticmethod
    def get_justify(code: str) -> Justify1D:
        """
        Get the justification enum from a justification code.
        Test coverage @ tests/test_feature1D.py
        :param code: string like "top" or similar
        :return: justify enum
        """
        return Justify1D.from_name(code)

    def __init__(
        self,
        asset: AssetResource,
        justify: typing.Union[str, Justify1D] = "center",
        direction: Direction = Direction.HORIZONTAL,
        overrides: typing.Optional[typing.List[Feature1DOverride]] = None,
    ):
        super().__init__(asset)
        if isinstance(justify, str):
            justify = Justify1D.from_name(justify)
        self.justify = justify
        self.direction = direction
        self.overrides: typing.Dict[int, Feature1DOverride] = {
            o.x: o for o in (overrides or [])
        }

    def tile(self, length: int):
        """
        Tile the asset to the given length.
        :param length: The length to tile to.
        :return: The tiled image.
        """
        img = self._asset.get()
        if self.direction == Direction.VERTICAL:
            img = img.transpose(Image.ROTATE_90)
        # Round up to the next multiple of the asset size...
        tiled = Image.new("RGBA", (odd(next_multiple(length, img.width)), img.height))
        tile_count = tiled.width // img.width
        # Calculate the "origin" tile
        center_pos = 0
        if self.justify == Justify1D.CENTER:
            center_pos = tile_count // 2
        elif self.justify == Justify1D.END:
            center_pos = tile_count - 1

        # Paste that thing all over the place
        for x in range(tile_count):
            vx = x - center_pos
            if vx in self.overrides:
                override = self.overrides[vx]
                tiled.paste(override.asset.get(), (x * img.width, 0))
            else:
                tiled.paste(img, (x * img.width, 0))

        # Crop to the desired size using the justification
        crop_from = 0
        if self.justify == Justify1D.CENTER:
            crop_from = (tiled.width - length) // 2
        elif self.justify == Justify1D.END:
            crop_from = tiled.width - length
        crop_to = crop_from + length
        tiled = tiled.crop((crop_from, 0, crop_to, img.height))
        if self.direction == Direction.VERTICAL:
            tiled = tiled.transpose(Image.ROTATE_270)
        return tiled

    @classmethod
    def import_(cls, json_body: JSON, theme_directory: typing.Optional[str] = None):
        if not isinstance(json_body, dict):
            raise ValidationError(
                f"JSON body for Feature should be a dict, not {json_body.__class__.__name__}",
                ValidationError.ErrorCode.WRONG_TYPE,
                "",
            )
        asset = AssetResource.import_(json_body, theme_directory)
        justify = json_body.get("justify", "center")
        if not isinstance(justify, str):
            raise ValidationError(
                f"JSON body for Feature justify should be a string, not {justify.__class__.__name__}",
                ValidationError.ErrorCode.WRONG_TYPE,
                ".justify",
            )
        raw_overrides = json_body.get("overrides", [])
        if not isinstance(raw_overrides, list):
            raise ValidationError(
                f"JSON body for Feature overrides should be a list, not {raw_overrides.__class__.__name__}",
                ValidationError.ErrorCode.WRONG_TYPE,
                ".overrides",
            )

        overrides: typing.List[Feature1DOverride] = []
        for i, o in enumerate(raw_overrides):
            try:
                overrides.append(Feature1DOverride.import_(o, theme_directory))
            except JSONTraceable as e:
                # re-contextualize
                e.extend(i)
                e.extend("overrides")
                raise e

        feature = check_feature(json_body, cls.FEATURE_TYPES)
        if feature in cls.HORIZONTAL_TYPES:
            direction = Direction.HORIZONTAL
        elif feature in cls.VERTICAL_TYPES:
            direction = Direction.VERTICAL
        else:
            raise ValueError(
                f"Unknown direction on feature type {feature} - report this as a bug!"
            )
        return cls(asset, justify, direction, overrides)
