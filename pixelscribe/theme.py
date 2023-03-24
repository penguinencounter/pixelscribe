import os.path
import typing

from pixelscribe import Feature, parser
from pixelscribe.contexts import FinalizeJsonErrors, JsonContext, JsonFileContext
from pixelscribe.overlay import Overlay
from pixelscribe.parser.reader import FilePosStorage


class Theme:
    def __init__(self, config_path: str, theme_dir: str, file_map: FilePosStorage):
        self.config_path = config_path
        self.theme_dir = theme_dir
        self.file_map = file_map
        self.features: typing.List[Feature] = []
        self.overlays: typing.List[Overlay] = []

    @classmethod
    def import_(cls, config_path: str):
        with open(config_path, "r") as f:
            config, file_map = parser.loads(f.read())
        theme_dir = os.path.dirname(config_path)  # effectively os.split(config_path)[0]
        with FinalizeJsonErrors(file_map), JsonFileContext(config_path):
            theme = cls(config_path, theme_dir, file_map)  # set up the container

            # initial validation setup
            if not isinstance(config, dict):
                raise TypeError(
                    "Theme config must be a dict, not a " + type(config).__name__
                )

            # load up the features
            if "features" not in config:
                features = []
            else:
                if isinstance(config["features"], list):
                    features = config["features"]
                else:
                    raise TypeError(
                        "Features must be a list, not a "
                        + type(config["features"]).__name__
                    )
            for i, feature in enumerate(features):
                with JsonContext("features", i):
                    theme.features.append(Feature.import_(feature, theme_dir))

            # load up the overlays
            if "overlays" not in config:
                overlays = []
            else:
                if isinstance(config["overlays"], list):
                    overlays = config["overlays"]
                else:
                    raise TypeError(
                        "Overlays must be a list, not a "
                        + type(config["overlays"]).__name__
                    )
            for i, overlay in enumerate(overlays):
                with JsonContext("overlays", i):
                    theme.overlays.append(Overlay.import_(overlay, theme_dir))
