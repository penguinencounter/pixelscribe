from PIL import Image

from pixelscribe import AssetResource
from pixelscribe.feature_2d import Feature2DOverride

i16 = Image.new("RGBA", (16, 16), (255, 0, 0, 255))
i16.paste(Image.new("RGBA", (14, 14), (0, 0, 0, 128)), (1, 1))
asset_resource_16 = AssetResource.from_image(i16)

i16_2 = Image.new("RGBA", (16, 16), (255, 255, 0, 255))
i16_2.paste(Image.new("RGBA", (14, 14), (0, 0, 0, 128)), (1, 1))
asset_resource_16_2 = AssetResource.from_image(i16_2)

i13 = Image.new("RGBA", (13, 13), (0, 0, 255, 255))
i13.alpha_composite(Image.new("RGBA", (11, 11), (0, 0, 0, 128)), (1, 1))
asset_resource_13 = AssetResource.from_image(i13)

override_2d_16 = Feature2DOverride(asset_resource_16_2, 0, 0)
override_2d_13 = Feature2DOverride(asset_resource_13, 0, 0)

i16h = Image.new("RGBA", (4, 16), (255, 0, 0, 0))
i16h.paste(Image.new("RGBA", (2, 14), (0, 0, 0, 128)), (1, 1))
asset_resource_horizontal_16 = AssetResource.from_image(i16h)

i16v = Image.new("RGBA", (16, 4), (255, 0, 0, 0))
i16v.paste(Image.new("RGBA", (14, 2), (0, 0, 0, 128)), (1, 1))

i13h = Image.new("RGBA", (3, 13), (255, 0, 0, 0))
i13h.paste(Image.new("RGBA", (1, 11), (0, 0, 0, 128)), (1, 1))
i13v = Image.new("RGBA", (13, 3), (255, 0, 0, 0))
i13v.paste(Image.new("RGBA", (11, 1), (0, 0, 0, 128)), (1, 1))
