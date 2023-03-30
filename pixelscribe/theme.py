import os.path
import typing

from PIL import Image

from pixelscribe import Feature, parser
from pixelscribe.contexts import FinalizeJsonErrors, JsonContext, JsonFileContext
from pixelscribe.exceptions import ValidationError
from pixelscribe.feature_1d import Feature1D
from pixelscribe.feature_2d import Feature2D
from pixelscribe.overlay import Anchor2D, Overlay
from pixelscribe.parser.reader import FilePosStorage


class Theme:
    def __init__(
        self,
        inherits_from: typing.Optional["Theme"],
        config_path: str,
        theme_dir: str,
        file_map: FilePosStorage,
    ):
        self.inherits_from = inherits_from
        self.config_path = config_path
        self.theme_dir = theme_dir
        self.file_map = file_map
        self.features: typing.List[Feature] = []
        self.overlays: typing.List[Overlay] = []
        self.colors: typing.Dict[str, typing.Tuple[int, int, int]] = {}

    FT = typing.TypeVar("FT", bound=Feature)

    def get_feature_by_type(
        self, feature_type: str, feature_object_type: typing.Type[FT]
    ) -> FT:
        for feature in self.features:
            if feature.feature_type == feature_type:
                if not isinstance(feature, feature_object_type):
                    raise TypeError(
                        f"Feature {feature_type} is not a {feature_object_type.__name__}, "
                        f"but a {type(feature).__name__}"
                    )
                return feature
        if self.inherits_from is not None:
            return self.inherits_from.get_feature_by_type(
                feature_type, feature_object_type
            )
        raise ValueError(f"Feature {feature_type} not found.")

    def layer1(self) -> typing.List[Overlay]:
        def filter_(overlay: Overlay) -> bool:
            return (
                overlay.anchor_mode == Anchor2D.AnchorMode.INSIDE and not overlay.above
            )

        return list(filter(filter_, self.overlays))

    def layer3(self) -> typing.List[Overlay]:
        def filter_(overlay: Overlay) -> bool:
            return overlay.above or overlay.anchor_mode != Anchor2D.AnchorMode.INSIDE

        return list(filter(filter_, self.overlays))

    def draw(
        self, width: int, height: int, text_layer: typing.Optional[Image.Image] = None
    ):
        # they need to have the same aspect ratio
        if text_layer is None:
            text_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        if text_layer.size[0] / text_layer.size[1] != width / height:
            raise ValueError(
                "Text layer must have the same aspect ratio as the output image (internal error)"
            )
        # create the bottom layer
        # background and borders
        layer0_size = [width, height]
        background = self.get_feature_by_type("background", Feature2D).tile(
            width, height
        )

        # how much space is already allocated to the corners and borders
        class Clearance(typing.NamedTuple):
            top: int
            bottom: int
            left: int
            right: int

            def __getitem__(
                self, item: typing.Union[str, int]
            ) -> int:  # index by names or indices
                if isinstance(item, str):
                    return getattr(self, item)
                return super().__getitem__(item)

            def __setitem__(self, key: str, value: int):
                setattr(self, key, value)

            def require(self, clear: int, side: str):
                if self[side] < clear:
                    self[side] = clear

        clearance = Clearance(0, 0, 0, 0)

        top_left_corner = self.get_feature_by_type("top_left_corner", Feature)
        clearance.require(top_left_corner.width, "left")
        clearance.require(top_left_corner.height, "top")

        top_right_corner = self.get_feature_by_type("top_right_corner", Feature)
        clearance.require(top_right_corner.width, "right")
        clearance.require(top_right_corner.height, "top")

        bottom_left_corner = self.get_feature_by_type("bottom_left_corner", Feature)
        clearance.require(bottom_left_corner.width, "left")
        clearance.require(bottom_left_corner.height, "bottom")

        bottom_right_corner = self.get_feature_by_type("bottom_right_corner", Feature)
        clearance.require(bottom_right_corner.width, "right")
        clearance.require(bottom_right_corner.height, "bottom")

        top_edge = self.get_feature_by_type("top_edge", Feature1D)
        clearance.require(top_edge.perpendicular, "top")
        left_edge = self.get_feature_by_type("left_edge", Feature1D)
        clearance.require(left_edge.perpendicular, "left")
        right_edge = self.get_feature_by_type("right_edge", Feature1D)
        clearance.require(right_edge.perpendicular, "right")
        bottom_edge = self.get_feature_by_type("bottom_edge", Feature1D)
        clearance.require(bottom_edge.perpendicular, "bottom")

        # for overlay in self.overlays:
        #     if overlay.anchor_mode == Anchor2D.AnchorMode.EDGE:
        #         affected_sides = []
        #         if overlay.anchor[]

    @classmethod
    def import_(cls, config_path: str):
        with open(config_path, "r") as f:
            config, file_map = parser.loads(f.read())
        theme_dir = os.path.dirname(config_path)  # effectively os.split(config_path)[0]
        with FinalizeJsonErrors(file_map), JsonFileContext(config_path):
            # TODO: inherit from other themes; defaults
            theme = cls(None, config_path, theme_dir, file_map)  # set up the container

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
