import os.path
import typing

from pixelscribe import Feature, parser
from pixelscribe.contexts import JsonFileContext
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
        with JsonFileContext(config_path):
            theme = cls(config_path, theme_dir, file_map)  # set up the container
            # import features

