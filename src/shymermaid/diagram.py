"""Shiny-free helpers that prepare Mermaid code and render options."""

from __future__ import annotations

import re
from typing import Any

DOCS_URL = "https://mermaid.js.org/intro/syntax-reference.html"

THEMES: dict[str, str] = {
    "default": "Default",
    "neutral": "Neutral",
    "dark": "Dark",
    "forest": "Forest",
    "base": "Base",
}

LOOKS: dict[str, str] = {
    "classic": "Classic",
    "handDrawn": "Hand drawn",
}

DIRECTIONS: dict[str, str] = {
    "asis": "As written",
    "TD": "Top to bottom",
    "BT": "Bottom to top",
    "LR": "Left to right",
    "RL": "Right to left",
}

DEFAULT_CODE = """\
flowchart TD
    subgraph A["<strong>Ingest</strong>"]
        a_in[/"<code>study.pdf</code>"/] --> a_run("Phases 1-8")
        a_run --> a_json[\\"<code>study.extract.json</code>"\\]
    end
    a_run -->|"<code>--db</code>"| kb[("<code>corpus.sqlite</code>")]
    subgraph B["<strong>Stage</strong>"]
        b_in[/"<code>blank_crf.pdf</code>"/] --> b_run("Phases 1-6")
        b_run --> b_xlsx[\\"<code>staging.xlsx</code>"\\]
    end
    kb -->|"<code>--corpus</code>"| b_run
    b_xlsx --> rev(["Reviewer"])
"""

_HEADER = re.compile(
    r"^(?P<indent>[ \t]*)(?P<kind>flowchart|graph)\b"
    r"(?:[ \t]+(?:TB|TD|BT|RL|LR)\b)?",
    re.MULTILINE,
)


def set_direction(code: str, direction: str) -> str:
    """Rewrite the first flowchart header to use ``direction``.

    ``"asis"`` returns ``code`` unchanged. Non flowchart diagrams are
    returned unchanged.
    """
    if direction not in DIRECTIONS:
        raise ValueError(f"Unknown direction: {direction!r}")
    if direction == "asis":
        return code
    return _HEADER.sub(lambda m: f"{m['indent']}{m['kind']} {direction}", code, count=1)


def render_config(theme: str, look: str) -> dict[str, Any]:
    """Build the options passed to ``mermaid.initialize()``."""
    if theme not in THEMES:
        raise ValueError(f"Unknown theme: {theme!r}")
    if look not in LOOKS:
        raise ValueError(f"Unknown look: {look!r}")
    return {
        "startOnLoad": False,
        "securityLevel": "strict",
        "theme": theme,
        "look": look,
    }
