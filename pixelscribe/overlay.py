import enum
import typing


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
