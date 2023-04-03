import pytest

from pixelscribe.theme import Theme, DEFAULT
from .test_import import get_full_tests


@pytest.mark.parametrize("hsize", [129, 128])
@pytest.mark.parametrize("vsize", [65, 64])
def test_does_the_default_work(hsize: int, vsize: int):
    DEFAULT.draw(hsize, vsize, None)


@pytest.mark.parametrize("target", map(lambda x: x[0], filter(lambda x: not x[1], get_full_tests())))
@pytest.mark.parametrize("hsize", [129, 128])
@pytest.mark.parametrize("vsize", [65, 64])
def test_themes(target: str, hsize: int, vsize: int):
    theme = Theme.import_(target)
    theme.draw(hsize, vsize, None)
