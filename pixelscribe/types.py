from typing import (  # would like to use TypeAlias, but we need 3.8 support
    Dict, List, Tuple, Union)

JSON = Union[Dict[str, "JSON"], List["JSON"], str, int, float, bool, None]
JSONObject = Dict[str, JSON]
IsInstanceType = Union[type, Tuple[type]]
