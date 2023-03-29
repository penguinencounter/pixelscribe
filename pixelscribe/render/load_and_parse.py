import copy
import os

import cmarkgfm  # type: ignore[reportMissingTypeStubs]
from bs4 import BeautifulSoup


def _gfm_to_html(markdown: str, options: int = 0) -> str:
    """hacky type stub for cmarkgfm.github_flavored_markdown_to_html"""
    return cmarkgfm.github_flavored_markdown_to_html(markdown, options)  # type:ignore


def render_markdown(source: str) -> BeautifulSoup:
    """Render markdown to html"""
    html = _gfm_to_html(source)
    souped = BeautifulSoup(html, "html.parser")
    ## Preprocessing
    # swap <pre><code> ... </pre></code> for <codeblock> ... </codeblock> keeping attributes
    for pre in souped.find_all("pre"):
        code = pre.find("code")
        if code is None:
            continue
        attrset = copy.deepcopy(code.attrs)
        attrset.update(pre.attrs)
        codeblock = souped.new_tag("codeblock", **attrset)  # type: ignore[reportUnknownArgumentType]
        codeblock.string = code.string
        pre.replace_with(codeblock)
    return souped


if __name__ == "__main__":
    source = ""
    console_marker = "md> " if os.isatty(0) else "."
    if not os.isatty(0):
        print("Reading", end="", flush=True)
    while True:
        source_line = input(console_marker)
        if source_line == "$$end":
            break
        source += source_line + "\n"
    soup = render_markdown(source)
    print()
    print(soup.prettify())
