from io import BytesIO
from PIL import ImageFont


def load_copy_font(file_path: str, font_size: int) -> ImageFont.FreeTypeFont:
    """Load a font file **into memory** and return a font"""
    with open(file_path, "rb") as font_file:
        return ImageFont.truetype(BytesIO(font_file.read()), font_size)