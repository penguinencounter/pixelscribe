from typing import (  # would like to use TypeAlias, but we need 3.8 support
    Dict,
    List,
    Union,
)

JSON = Union[Dict[str, "JSON"], List["JSON"], str, int, float, bool, None]
JSONObject = Dict[str, JSON]
JSONArray = List[JSON]
