from pixelscribe.overlay import Anchor2D

verbose = {
    "top left": (Anchor2D.X.LEFT, Anchor2D.Y.TOP),
    "top center": (Anchor2D.X.CENTER, Anchor2D.Y.TOP),
    "top right": (Anchor2D.X.RIGHT, Anchor2D.Y.TOP),
    "center left": (Anchor2D.X.LEFT, Anchor2D.Y.CENTER),
    "center center": (Anchor2D.X.CENTER, Anchor2D.Y.CENTER),
    "center right": (Anchor2D.X.RIGHT, Anchor2D.Y.CENTER),
    "bottom left": (Anchor2D.X.LEFT, Anchor2D.Y.BOTTOM),
    "bottom center": (Anchor2D.X.CENTER, Anchor2D.Y.BOTTOM),
    "bottom right": (Anchor2D.X.RIGHT, Anchor2D.Y.BOTTOM),
    "inside-top right": (Anchor2D.X.RIGHT, Anchor2D.Y.INSIDE_TOP),
    "inside-top left": (Anchor2D.X.LEFT, Anchor2D.Y.INSIDE_TOP),
    "inside-bottom right": (Anchor2D.X.RIGHT, Anchor2D.Y.INSIDE_BOTTOM),
    "inside-bottom left": (Anchor2D.X.LEFT, Anchor2D.Y.INSIDE_BOTTOM),
}
one_word = {
    "center": (Anchor2D.X.CENTER, Anchor2D.Y.CENTER),
    "left": (Anchor2D.X.LEFT, Anchor2D.Y.CENTER),
    "right": (Anchor2D.X.RIGHT, Anchor2D.Y.CENTER),
    "top": (Anchor2D.X.CENTER, Anchor2D.Y.TOP),
    "bottom": (Anchor2D.X.CENTER, Anchor2D.Y.BOTTOM),
}
all_anchors = {**verbose, **one_word}


def test_anchor2d_parsing():
    pass
