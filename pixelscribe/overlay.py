import enum
import typing

from pixelscribe import JSON, AssetResource, ValidationError, get_justify


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
        INSIDE_LEFT = "inside-left", ("outside", "edge")
        INSIDE_RIGHT = "inside-right", ("outside", "edge")

        def __repr__(self):
            return f"{self.value[0]}"

        @staticmethod
        def valid(
            x_anchor: "Anchor2D.X", anchor: "Anchor2D.AnchorMode"
        ) -> typing.Tuple[bool, str]:
            if x_anchor.value[1] is None:
                return True, ""
            if anchor.value in x_anchor.value[1]:
                return True, ""
            return (
                False,
                f"Anchor {x_anchor.value[0]} cannot be used in mode {anchor.value}",
            )

    @enum.unique
    class Y(enum.Enum):
        TOP = "top", None
        CENTER = "center", None
        BOTTOM = "bottom", None
        INSIDE_TOP = "inside-top", ("outside", "edge")
        INSIDE_BOTTOM = "inside-bottom", ("outside", "edge")

        def __repr__(self):
            return f"{self.value[0]}"

        @staticmethod
        def valid(
            y_anchor: "Anchor2D.Y", anchor: "Anchor2D.AnchorMode"
        ) -> typing.Tuple[bool, str]:
            if y_anchor.value[1] is None:
                return True, ""
            if anchor.value in y_anchor.value[1]:
                return True, ""
            return (
                False,
                f"Anchor {y_anchor.value[0]} cannot be used in mode {anchor.value}",
            )

    ONLY_ONE_OF = (X.INSIDE_LEFT, X.INSIDE_RIGHT, Y.INSIDE_TOP, Y.INSIDE_BOTTOM)
    NOT_WITH_CENTER = (X.INSIDE_LEFT, X.INSIDE_RIGHT, Y.INSIDE_TOP, Y.INSIDE_BOTTOM)
    OUTSIDE_DISALLOWED = ((X.CENTER, Y.CENTER),)

    anchor_modes = {
        "inside": AnchorMode.INSIDE,
        "outside": AnchorMode.OUTSIDE,
        "edge": AnchorMode.EDGE,
    }

    x_word = {
        "left": X.LEFT,
        "center": X.CENTER,
        "right": X.RIGHT,
        "inside-left": X.INSIDE_LEFT,
        "inside-right": X.INSIDE_RIGHT,
    }
    y_word = {
        "top": Y.TOP,
        "center": Y.CENTER,
        "bottom": Y.BOTTOM,
        "inside-top": Y.INSIDE_TOP,
        "inside-bottom": Y.INSIDE_BOTTOM,
    }
    one_word_aliases = {
        "center": ("center", "center"),
        "left": ("center", "left"),
        "right": ("center", "right"),
        "top": ("top", "center"),
        "bottom": ("bottom", "center"),
    }

    @staticmethod
    def valid(
        x_anchor: typing.Union[X, str],
        y_anchor: typing.Union[Y, str],
        anchor: typing.Union[AnchorMode, str],
    ) -> typing.Tuple[bool, str]:
        if isinstance(x_anchor, str):
            x_anchor = Anchor2D.X(x_anchor.upper())
        if isinstance(y_anchor, str):
            y_anchor = Anchor2D.Y(y_anchor.upper())
        if isinstance(anchor, str):
            anchor = Anchor2D.AnchorMode(anchor.upper())
        if anchor != Anchor2D.AnchorMode.INSIDE:
            if (x_anchor, y_anchor) in Anchor2D.OUTSIDE_DISALLOWED:
                return (
                    False,
                    f"Cannot use '{x_anchor.value[0]}' and '{y_anchor.value[0]}' together in mode '{anchor.value}'",
                )
            if x_anchor in Anchor2D.NOT_WITH_CENTER and y_anchor == Anchor2D.Y.CENTER:
                return (
                    False,
                    "Cannot use 'center' with 'inside-left', 'inside-right', 'inside-top', or 'inside-bottom'",
                )
            if y_anchor in Anchor2D.NOT_WITH_CENTER and x_anchor == Anchor2D.X.CENTER:
                return (
                    False,
                    "Cannot use 'center' with 'inside-left', 'inside-right', 'inside-top', or 'inside-bottom'",
                )
        x_valid = Anchor2D.X.valid(x_anchor, anchor)
        if not x_valid[0]:
            return x_valid
        y_valid = Anchor2D.Y.valid(y_anchor, anchor)
        if not y_valid[0]:
            return y_valid
        if x_anchor in Anchor2D.ONLY_ONE_OF and y_anchor in Anchor2D.ONLY_ONE_OF:
            return (
                False,
                "Cannot use more than one of 'inside-left', 'inside-right', 'inside-top', or 'inside-bottom'",
            )
        return True, ""


class Overlay:
    def __init__(
        self,
        asset: AssetResource,
        anchor_mode: typing.Union[
            str, Anchor2D.AnchorMode
        ] = Anchor2D.AnchorMode.INSIDE,
        anchor: typing.Union[str, typing.Tuple[Anchor2D.X, Anchor2D.Y]] = "center",
    ):
        self._asset = asset
        if isinstance(anchor_mode, str):
            if anchor_mode not in Anchor2D.anchor_modes:
                raise ValidationError(
                    f"Invalid anchor mode: {anchor_mode}",
                    ValidationError.ErrorCode.INVALID_VALUE,
                )
            self.anchor_mode = Anchor2D.anchor_modes[anchor_mode]
        else:
            self.anchor_mode = anchor_mode
        if isinstance(anchor, str):
            # try to import it
            anc = get_justify(
                anchor, Anchor2D.one_word_aliases, Anchor2D.x_word, Anchor2D.y_word
            )
            # validate...
            valid = Anchor2D.valid(anc[0], anc[1], self.anchor_mode)
            if not valid[0]:
                raise ValidationError(valid[1], ValidationError.ErrorCode.INVALID_VALUE)
            self.anchor = anc
        else:
            # assume this is not already validated for safety
            valid = Anchor2D.valid(anchor[0], anchor[1], self.anchor_mode)
            if not valid[0]:
                raise ValidationError(valid[1], ValidationError.ErrorCode.INVALID_VALUE)
            self.anchor = anchor

    @classmethod
    def import_(cls, json_body: JSON, theme_directory: typing.Optional[str] = None):
        if not isinstance(json_body, dict):
            raise ValidationError(
                f"JSON body for Overlay should be a dict, not {json_body.__class__.__name__}",
                ValidationError.ErrorCode.WRONG_TYPE,
            )
        # TEMPORARY: TODO: remove ignore
        asset = AssetResource.import_(json_body, theme_directory)  # type: ignore
