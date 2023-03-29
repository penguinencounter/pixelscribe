import cmarkgfm  # type: ignore[reportMissingTypeStubs]
from bs4 import BeautifulSoup


def _gfm_to_html(markdown: str, options: int = 0) -> str:
    """hacky type stub for cmarkgfm.github_flavored_markdown_to_html"""
    return cmarkgfm.github_flavored_markdown_to_html(markdown, options)  # type:ignore


def render_markdown() -> BeautifulSoup:
    """Render markdown to html"""
    with open("README.md", "r") as f:
        markdown = f.read()
    html = _gfm_to_html(markdown)
    return BeautifulSoup(html, "html.parser")
