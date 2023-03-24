import os.path
import typing

from pixelscribe import Feature, parser
from pixelscribe.contexts import FinalizeJsonErrors, JsonContext, JsonFileContext
from pixelscribe.exceptions import ValidationError
from pixelscribe.feature_1d import Feature1D
from pixelscribe.feature_2d import Feature2D
from pixelscribe.overlay import Overlay
from pixelscribe.parser.reader import FilePosStorage


class Theme:
    def __init__(self, config_path: str, theme_dir: str, file_map: FilePosStorage):
        self.config_path = config_path
        self.theme_dir = theme_dir
        self.file_map = file_map
        self.features: typing.List[Feature] = []
        self.overlays: typing.List[Overlay] = []
        self.colors: typing.Dict[str, typing.Tuple[int, int, int]] = {}

    @classmethod
    def import_(cls, config_path: str):
        with open(config_path, "r") as f:
            config, file_map = parser.loads(f.read())
        theme_dir = os.path.dirname(config_path)  # effectively os.split(config_path)[0]
        with FinalizeJsonErrors(file_map), JsonFileContext(config_path):
            theme = cls(config_path, theme_dir, file_map)  # set up the container

            # initial validation setup
            if not isinstance(config, dict):
                raise ValidationError(
                    "Theme config must be a dict, not a " + type(config).__name__,
                    ValidationError.ErrorCode.WRONG_TYPE,
                    "",
                )

            # load up the features
            if "features" not in config:
                features = []
            else:
                if isinstance(config["features"], list):
                    features = config["features"]
                else:
                    raise ValidationError(
                        "Features must be a list, not a "
                        + type(config["features"]).__name__,
                        ValidationError.ErrorCode.WRONG_TYPE,
                        "features",
                    )
            for i, feature in enumerate(features):
                with JsonContext("features", i):
                    # try to load up the feature type first...
                    feature_type = Feature.get_feature_type(feature)
                    # pick the correct type
                    if feature_type in Feature.FEATURE_TYPES:
                        theme.features.append(Feature.import_(feature, theme_dir))
                    elif feature_type in Feature1D.FEATURE_TYPES:
                        theme.features.append(Feature1D.import_(feature, theme_dir))
                    elif feature_type in Feature2D.FEATURE_TYPES:
                        theme.features.append(Feature2D.import_(feature, theme_dir))
                    else:
                        raise ValidationError(
                            "Unknown feature type: '"
                            + feature_type
                            + "' while importing theme.",
                            ValidationError.ErrorCode.INVALID_VALUE,
                            "",  # handled by context manager
                        )

            # load up the overlays
            if "overlays" not in config:
                overlays = []
            else:
                if isinstance(config["overlays"], list):
                    overlays = config["overlays"]
                else:
                    raise ValidationError(
                        "Overlays must be a list, not a "
                        + type(config["overlays"]).__name__,
                        ValidationError.ErrorCode.WRONG_TYPE,
                        "overlays",
                    )
            for i, overlay in enumerate(overlays):
                with JsonContext("overlays", i):
                    theme.overlays.append(Overlay.import_(overlay, theme_dir))

            # load up the colors(?)
            if "colors" not in config:
                colors = {}
            else:
                if isinstance(config["colors"], dict):
                    colors = config["colors"]
                else:
                    raise ValidationError(
                        "Colors must be a dict, not a "
                        + type(config["colors"]).__name__,
                        ValidationError.ErrorCode.WRONG_TYPE,
                        "colors",
                    )
            for color_name, color in colors.items():
                with JsonContext("colors", color_name):
                    if not isinstance(color, str):
                        raise ValidationError(
                            "Color values must be strings, not a "
                            + type(color).__name__,
                            ValidationError.ErrorCode.WRONG_TYPE,
                            color_name,
                        )
                    if color[0] != "#":
                        raise ValidationError(
                            "Color values must be hex strings (start it with a #)",
                            ValidationError.ErrorCode.INVALID_VALUE,
                            color_name,
                        )
                    if len(color) != 7:
                        raise ValidationError(
                            f"Color values must have 6 hexadecimal characters, not {len(color) - 1}",
                            ValidationError.ErrorCode.INVALID_VALUE,
                            color_name,
                        )
                    for char in color[1:]:
                        if char not in "0123456789abcdefABCDEF":
                            raise ValidationError(
                                f"Color values must be hex strings, not {char}",
                                ValidationError.ErrorCode.INVALID_VALUE,
                                color_name,
                            )
                    color_data = (
                        int(color[1:3], 16),
                        int(color[3:5], 16),
                        int(color[5:7], 16),
                    )
                    theme.colors[color_name] = color_data
            return theme  # all done!
