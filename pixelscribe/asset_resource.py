import enum
import os
import os.path
import re
import typing

from PIL import Image

from .exceptions import ValidationError
from .types import JSON, JSONObject


def _normalize(path: str) -> str:
    """
    Standardize a path to a file, hopefully making it the same regardless of relative paths.
    :param path: The path to normalize.
    :return: The normalized path.
    """
    return os.path.abspath(os.path.expanduser(path))


def next_multiple(value: int, multiple: int) -> int:
    """
    Get the next multiple of a number.
    :param value: The value to round up.
    :param multiple: The multiple to round up to.
    :return: The next multiple.
    """
    return value + (multiple - value % multiple)


def odd(value: int) -> int:
    """
    Get the next odd number.
    :param value: The value to round up.
    :return: The next odd number.
    """
    return value + 1 if value % 2 == 0 else value


def check_feature(json_body: JSONObject, allowed: typing.List[str]) -> str:
    if "feature" not in json_body:
        raise ValidationError(
            'Feature(s) require a "feature".',
            ValidationError.ErrorCode.MISSING_VALUE,
        )
    feature = json_body["feature"]
    if not isinstance(feature, str):
        raise ValidationError(
            f'Feature(s) require a "feature" of type string, not {feature.__class__.__name__}.',
            ValidationError.ErrorCode.WRONG_TYPE,
        )

    if feature not in allowed:
        msg = (
            f'JSON body for Feature feature should be a valid 0-dimensional feature, not "{feature}".\n'
            f"Valid features are:\n"
        )
        for feature_type in allowed:
            msg += f"  {feature_type}\n"
        msg = msg[:-1]
        raise ValidationError(
            msg,
            ValidationError.ErrorCode.INVALID_VALUE,
        )
    return feature


shared_asset_cache: typing.Dict[str, Image.Image] = {}


class AssetResource:
    """
    Represents an image asset that is used during the compositing process.
    """

    def __init__(
        self,
        source: str,
        crop: typing.Optional[typing.Tuple[int, int, int, int]] = None,
        source_image: typing.Optional[Image.Image] = None,
    ):
        self.source_path = _normalize(source)
        self._static = False
        self.source: Image.Image = source_image or self._load()
        if crop is None:
            self.crop: typing.Tuple[int, int, int, int] = (
                0,
                0,
                self.source.width,
                self.source.height,
            )
        else:
            self.crop: typing.Tuple[int, int, int, int] = crop

    def _load(self) -> Image.Image:
        """
        Load the source image into memory.
        :return:
        """
        if self._static:
            return self.source
        if self.source_path in shared_asset_cache:
            return shared_asset_cache[self.source_path]
        else:
            source: Image.Image = Image.open(self.source_path).convert("RGBA")
            source.load()
            shared_asset_cache[self.source_path] = source
            return source

    def get(self) -> Image.Image:
        """
        Get the source image, cropped.
        :return:
        """
        return self.source.crop(self.crop)

    @classmethod
    def import_(
        cls, json_body: JSON, theme_directory: typing.Optional[str] = None
    ) -> "AssetResource":
        """
        Import an AssetResource from JSON.
        This is the code side of #/definitions/sourced in the theme schema.
        Specification should be managed in the schema, then ported to here.
        :param json_body: JSON python representation, by json.load[s].
        :param theme_directory: Path of the theme file or None for the cwd
        :return: ...new
        """
        theme_directory = (
            theme_directory or os.getcwd()
        )  # ideally don't support this later
        if not isinstance(json_body, dict):
            raise ValidationError(
                f"JSON body for AssetResource should be a dict, not {json_body.__class__.__name__}",
                ValidationError.ErrorCode.WRONG_TYPE,
            )
        # required: source
        if "source" not in json_body:
            raise ValidationError(
                'AssetResource(s) require a "source".',
                ValidationError.ErrorCode.MISSING_VALUE,
            )
        source = json_body["source"]  # relative to theme file
        if not isinstance(source, str):
            raise ValidationError(
                f"JSON body for AssetResource source should be a string, not {source.__class__.__name__}",
                ValidationError.ErrorCode.WRONG_TYPE,
            )
        # IF there is a crop, it must be exactly four integers.
        if "crop" in json_body:
            crop = json_body["crop"]
            if not isinstance(crop, list):
                raise ValidationError(
                    f"JSON body for AssetResource crop should be a list, not {crop.__class__.__name__}",
                    ValidationError.ErrorCode.WRONG_TYPE,
                )
            if len(crop) != 4:
                raise ValidationError(
                    f'"crop" must be exactly 4 integers or omitted, got {len(crop)} instead',
                    ValidationError.ErrorCode.INVALID_VALUE,
                )
            intermediate: typing.List[int] = []
            for crop_att in crop:
                try:
                    assert (
                        isinstance(crop_att, float) and crop_att.is_integer()
                    ) or isinstance(crop_att, int)
                    assert int(crop_att) >= 0
                    intermediate.append(int(crop_att))
                except (ValueError, AssertionError):
                    raise ValidationError(
                        f"Cropping values must be integers that are at least 0. (got {crop_att})",
                        ValidationError.ErrorCode.INVALID_VALUE,
                    )
            # noinspection PyTypeChecker
            new_crop: typing.Optional[typing.Tuple[int, int, int, int]] = tuple(
                intermediate
            )
        else:
            new_crop = None
        # try to resolve the source path on the theme path if it's not absolute
        if not os.path.isabs(source):
            source = os.path.join(theme_directory, source)
        # ensure it's absolute and all that
        source = _normalize(source)
        return cls(source, new_crop)

    @classmethod
    def from_image(cls, image: Image.Image):
        i = cls("", None, image)
        i._static = True
        return i


class Feature:
    FEATURE_TYPES = [
        "top_left_corner",
        "top_right_corner",
        "bottom_left_corner",
        "bottom_right_corner",
        "block_quote_top_cap",
        "block_quote_bottom_cap",
        "code_top_left_corner",
        "code_top_right_corner",
        "code_bottom_left_corner",
        "code_bottom_right_corner",
        "horizontal_rule_left_cap",
        "horizontal_rule_right_cap",
        "bullet",
    ]

    def __init__(self, asset: AssetResource):
        self._asset = asset

    @classmethod
    def import_(cls, json_body: JSON, theme_directory: typing.Optional[str] = None):
        if not isinstance(json_body, dict):
            raise ValidationError(
                f"JSON body for Feature should be a dict, not {json_body.__class__.__name__}",
                ValidationError.ErrorCode.WRONG_TYPE,
            )
        asset = AssetResource.import_(json_body, theme_directory)
        if "feature" not in json_body:
            raise ValidationError(
                'Feature(s) require a "feature".',
                ValidationError.ErrorCode.MISSING_VALUE,
            )
        check_feature(json_body, cls.FEATURE_TYPES)

        return cls(asset)


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


class Anchor2D:
    @enum.unique
    class AnchorMode(enum.Enum):
        INSIDE = "inside"
        OUTSIDE = "outside"
        EDGE = "edge"

    @enum.unique
    class X(enum.Enum):
        LEFT = "left", None
        CENTER = "center", None
        RIGHT = "right", None
        INSIDE_LEFT = "inside-left", ("outside",)
        INSIDE_RIGHT = "inside-right", ("outside",)

        def __repr__(self):
            return f"{self.value[0]}"

        @staticmethod
        def valid(x_anchor: "Anchor2D.X", anchor: "Anchor2D.AnchorMode") -> bool:
            return x_anchor.value[1] is None or anchor.value in x_anchor.value[1]

    @enum.unique
    class Y(enum.Enum):
        TOP = "top", None
        CENTER = "center", None
        BOTTOM = "bottom", None
        INSIDE_TOP = "inside-top", ("outside",)
        INSIDE_BOTTOM = "inside-bottom", ("outside",)

        def __repr__(self):
            return f"{self.value[0]}"

        @staticmethod
        def valid(y_anchor: "Anchor2D.Y", anchor: "Anchor2D.AnchorMode") -> bool:
            return y_anchor.value[1] is None or anchor.value in y_anchor.value[1]

    ONLY_ONE_OF = (X.INSIDE_LEFT, X.INSIDE_RIGHT, Y.INSIDE_TOP, Y.INSIDE_BOTTOM)

    @staticmethod
    def valid(
        x_anchor: typing.Union[X, str],
        y_anchor: typing.Union[Y, str],
        anchor: typing.Union[AnchorMode, str],
    ) -> bool:
        if isinstance(x_anchor, str):
            x_anchor = Anchor2D.X(x_anchor.upper())
        if isinstance(y_anchor, str):
            y_anchor = Anchor2D.Y(y_anchor.upper())
        if isinstance(anchor, str):
            anchor = Anchor2D.AnchorMode(anchor.upper())
        return (
            Anchor2D.X.valid(x_anchor, anchor)
            and Anchor2D.Y.valid(y_anchor, anchor)
            and not (
                x_anchor in Anchor2D.ONLY_ONE_OF and y_anchor in Anchor2D.ONLY_ONE_OF
            )
        )


@enum.unique
class Justify1D(enum.Enum):
    START = "start"
    CENTER = "center"
    END = "end"

    @classmethod
    def from_name(cls, name: str) -> "Justify1D":
        return {
            "start": cls.START,
            "center": cls.CENTER,
            "end": cls.END,
            "left": cls.START,
            "right": cls.END,
            "top": cls.START,
            "bottom": cls.END,
        }[name.lower()]


@enum.unique
class Direction(enum.Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"

    @classmethod
    def from_name(cls, name: str) -> "Direction":
        return {"horizontal": cls.HORIZONTAL, "vertical": cls.VERTICAL}[name.lower()]


class FeatureOverride:
    def __init__(self, asset: AssetResource):
        self.asset = asset


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
        index = typing.cast(typing.List[int | float], index)
        return cls(asset, int(index[0]), int(index[1]))


class Feature2D(Feature):
    FEATURE_TYPES = ["background", "code_background"]

    @staticmethod
    def get_justify(code: str) -> typing.Tuple[Justify2D.X, Justify2D.Y]:
        """
        Get the justification enums from a justification code.
        Test coverage @ tests/test_feature2D.py
        :param code: string like "top left" or similar
        :return: (x justify, y justify)
        """
        words = re.findall(
            r"(?:^|(?<=[^A-Za-z0-9]))(\w+)(?=[^A-Za-z0-9]|$)", code.lower()
        )
        if 1 < len(words) > 2:
            raise ValidationError(
                f"Invalid justify code: {code}; must be 1 or 2 words, got {len(words)}",
                ValidationError.ErrorCode.INVALID_VALUE,
            )
        if len(words) == 1:
            if words[0] in Justify2D.one_word_aliases:
                words = Justify2D.one_word_aliases[words[0]]
            else:
                raise ValidationError(
                    f"Invalid justify code: {code}; the 1-word code '{words[0]}' is not supported",
                    ValidationError.ErrorCode.INVALID_VALUE,
                )
        if words[1] not in Justify2D.x_word:
            raise ValidationError(
                f"Invalid justify code: {code}; the second word '{words[1]}' is not a supported x justification",
                ValidationError.ErrorCode.INVALID_VALUE,
            )
        if words[0] not in Justify2D.y_word:
            raise ValidationError(
                f"Invalid justify code: {code}; the first word '{words[0]}' is not a supported y justification",
                ValidationError.ErrorCode.INVALID_VALUE,
            )
        justify = Justify2D.x_word[words[1]], Justify2D.y_word[words[0]]
        return justify

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
            justify = self.get_justify(justify)
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


class Feature1DOverride(FeatureOverride):
    def __init__(self, asset: AssetResource, x: int):
        super().__init__(asset)
        self.x = x


class Feature1D(Feature):
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


if __name__ == "__main__":
    pass
