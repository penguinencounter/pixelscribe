import os
import os.path
import re
import typing
from enum import Enum

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


_JustifyXType = typing.TypeVar("_JustifyXType", bound=Enum)
_JustifyYType = typing.TypeVar("_JustifyYType", bound=Enum)


def get_justify(
    code: str,
    one_word: typing.Dict[str, typing.Tuple[str, str]],
    x_set: typing.Dict[str, _JustifyXType],
    y_set: typing.Dict[str, _JustifyYType],
) -> typing.Tuple[_JustifyXType, _JustifyYType]:
    """
    Get the justification enums from a justification code.
    Test coverage @ tests/test_feature2D.py

    @param code: string like "top left" or similar
    @param one_word: dict of 1-word codes to (x str alias, y str alias)
    @param x_set: dict of x codes to x justify
    @param y_set: dict of y codes to y justify
    @return: (x justify, y justify)
    """
    words = re.findall(r"(?:^|(?<=[^A-Za-z0-9]))(\w+)(?=[^A-Za-z0-9]|$)", code.lower())
    if 1 < len(words) > 2:
        raise ValidationError(
            f"Invalid justify code: {code}; must be 1 or 2 words, got {len(words)}",
            ValidationError.ErrorCode.INVALID_VALUE,
        )
    if len(words) == 1:
        if words[0] in one_word:
            words = one_word[words[0]]
        else:
            raise ValidationError(
                f"Invalid justify code: {code}; the 1-word code '{words[0]}' is not supported",
                ValidationError.ErrorCode.INVALID_VALUE,
            )
    if words[1] not in x_set:
        raise ValidationError(
            f"Invalid justify code: {code}; the second word '{words[1]}' is not a supported x justification",
            ValidationError.ErrorCode.INVALID_VALUE,
        )
    if words[0] not in y_set:
        raise ValidationError(
            f"Invalid justify code: {code}; the first word '{words[0]}' is not a supported y justification",
            ValidationError.ErrorCode.INVALID_VALUE,
        )
    justify = x_set[words[1]], y_set[words[0]]
    return justify


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


class FeatureOverride:
    def __init__(self, asset: AssetResource):
        self.asset = asset


if __name__ == "__main__":
    pass
