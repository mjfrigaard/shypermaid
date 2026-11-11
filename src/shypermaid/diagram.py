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

LAYOUTS: dict[str, str] = {
    "dagre": "Dagre",
    "elk": "ELK",
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

_DIRS = r"(?:TB|TD|BT|RL|LR)"
_FLOWCHART = re.compile(
    rf"^(?P<head>[ \t]*(?:flowchart-elk|flowchart|graph))(?:[ \t]+{_DIRS})?(?![\w-])"
)
_GITGRAPH = re.compile(
    r"^(?P<head>[ \t]*gitGraph)(?![\w-])(?:[ \t]+(?:TB|BT|LR))?[ \t]*:?"
)
_STATEMENT = re.compile(r"^[ \t]*(?:stateDiagram|classDiagram)(?:-v2)?(?![\w-])")
_DIRECTION_LINE = re.compile(rf"^(?P<indent>[ \t]*)direction[ \t]+{_DIRS}(?=\s|$)")


def _declaration(lines: list[str]) -> int | None:
    """Index of the diagram type line, after frontmatter and ``%%`` lines."""
    i, n = 0, len(lines)
    while i < n and not lines[i].strip():
        i += 1
    if i < n and lines[i].strip() == "---":
        i += 1
        while i < n and lines[i].strip() != "---":
            i += 1
        i += 1
    while i < n and (not lines[i].strip() or lines[i].lstrip().startswith("%%")):
        i += 1
    return i if i < n else None


def _set_statement(lines: list[str], decl: int, direction: str) -> list[str]:
    """Set the top level ``direction`` statement of a state or class diagram."""
    depth = 0
    for i in range(decl + 1, len(lines)):
        line = lines[i]
        if line.lstrip().startswith("%%"):
            continue
        m = _DIRECTION_LINE.match(line)
        if depth == 0 and m:
            lines[i] = _DIRECTION_LINE.sub(f"{m['indent']}direction {direction}", line)
            return lines
        depth += line.count("{") - line.count("}")
    body = [ln for ln in lines[decl + 1 :] if ln.strip()]
    indent = body[0][: len(body[0]) - len(body[0].lstrip())] if body else "    "
    if not lines[decl].endswith("\n"):
        lines[decl] += "\n"
    lines.insert(decl + 1, f"{indent}direction {direction}\n")
    return lines


def set_direction(code: str, direction: str) -> str:
    """Rewrite the direction of a flowchart, state, class, or git graph diagram.

    Only the diagram type line (after any frontmatter and ``%%`` lines) and,
    for state and class diagrams, the top level ``direction`` statement are
    changed:

    * ``flowchart``, ``flowchart-elk``, and ``graph``: the header direction.
    * ``stateDiagram`` and ``classDiagram``: a ``direction`` statement is
      replaced or added. ``"TD"`` is written as ``TB``.
    * ``gitGraph``: the header (``gitGraph TB:``). ``"TD"`` is written as
      ``TB``; ``"RL"`` is not supported and leaves the code unchanged.

    ``"asis"`` and every other diagram type return ``code`` unchanged.

    Parameters
    ----------
    code
        Mermaid source.
    direction
        A key of ``DIRECTIONS``: ``"asis"``, ``"TD"``, ``"BT"``, ``"LR"``,
        or ``"RL"``.

    Returns
    -------
    str
        The code with its direction rewritten.

    Raises
    ------
    ValueError
        If ``direction`` is not a key of ``DIRECTIONS``.

    Examples
    --------
    >>> set_direction("flowchart TD", "LR")
    'flowchart LR'
    >>> set_direction("classDiagram", "RL")
    'classDiagram\\n    direction RL\\n'
    """
    if direction not in DIRECTIONS:
        raise ValueError(f"Unknown direction: {direction!r}")
    if direction == "asis":
        return code
    lines = code.splitlines(keepends=True)
    decl = _declaration(lines)
    if decl is None:
        return code
    line = lines[decl]
    tb = "TB" if direction == "TD" else direction
    if m := _FLOWCHART.match(line):
        lines[decl] = f"{m['head']} {direction}{line[m.end() :]}"
    elif m := _GITGRAPH.match(line):
        if tb == "RL":
            return code
        lines[decl] = f"{m['head']} {tb}:{line[m.end() :]}"
    elif _STATEMENT.match(line):
        lines = _set_statement(lines, decl, tb)
    return "".join(lines)


def render_config(theme: str, look: str, layout: str = "dagre") -> dict[str, Any]:
    """Build the options passed to ``mermaid.initialize()``.

    Parameters
    ----------
    theme
        A key of ``THEMES``.
    look
        A key of ``LOOKS``.
    layout
        A key of ``LAYOUTS``. Mermaid 12 includes the ELK layout, so
        ``"elk"`` needs no plugin.

    Returns
    -------
    dict[str, Any]
        Options with ``startOnLoad`` off and ``securityLevel`` strict.

    Raises
    ------
    ValueError
        If ``theme``, ``look``, or ``layout`` is unknown.

    Examples
    --------
    >>> render_config("dark", "classic")["theme"]
    'dark'
    """
    if theme not in THEMES:
        raise ValueError(f"Unknown theme: {theme!r}")
    if look not in LOOKS:
        raise ValueError(f"Unknown look: {look!r}")
    if layout not in LAYOUTS:
        raise ValueError(f"Unknown layout: {layout!r}")
    return {
        "startOnLoad": False,
        "securityLevel": "strict",
        "theme": theme,
        "look": look,
        "layout": layout,
    }
