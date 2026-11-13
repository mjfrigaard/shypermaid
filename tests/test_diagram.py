import pytest

from shypermaid.diagram import DEFAULT_CODE, code_theme, render_config, set_direction


def test_set_direction_replaces_existing():
    assert set_direction("flowchart TD\n  a --> b", "LR") == "flowchart LR\n  a --> b"


def test_set_direction_adds_missing():
    assert set_direction("graph\n  a --> b", "RL") == "graph RL\n  a --> b"


def test_set_direction_keeps_frontmatter_and_subgraph():
    code = "---\nconfig:\n  theme: dark\n---\nflowchart TD\n  subgraph X\n  end"
    out = set_direction(code, "BT")
    assert "flowchart BT" in out
    assert "subgraph X" in out
    assert out.startswith("---\nconfig:")


def test_set_direction_asis_and_non_flowchart():
    assert set_direction(DEFAULT_CODE, "asis") == DEFAULT_CODE
    seq = "sequenceDiagram\n  A->>B: hi"
    assert set_direction(seq, "LR") == seq


def test_set_direction_invalid():
    with pytest.raises(ValueError):
        set_direction("flowchart TD", "XX")


def test_render_config():
    cfg = render_config("dark", "handDrawn")
    assert cfg["theme"] == "dark"
    assert cfg["look"] == "handDrawn"
    assert cfg["startOnLoad"] is False


def test_render_config_layout():
    assert render_config("dark", "classic")["layout"] == "dagre"
    assert render_config("dark", "classic", "elk")["layout"] == "elk"


@pytest.mark.parametrize(
    "theme,look,layout",
    [
        ("nope", "classic", "dagre"),
        ("dark", "nope", "dagre"),
        ("dark", "classic", "nope"),
    ],
)
def test_render_config_invalid(theme, look, layout):
    with pytest.raises(ValueError):
        render_config(theme, look, layout)


def test_set_direction_flowchart_elk_header():
    assert set_direction("flowchart-elk TD\n  a --> b", "LR") == (
        "flowchart-elk LR\n  a --> b"
    )


def test_set_direction_only_touches_declaration_line():
    code = "stateDiagram-v2\n    graph --> x"
    assert (
        set_direction(code, "LR")
        == "stateDiagram-v2\n    direction LR\n    graph --> x"
    )
    flow = "flowchart TD\n  graph --> b"
    assert set_direction(flow, "LR") == "flowchart LR\n  graph --> b"


def test_set_direction_skips_comments_and_frontmatter():
    code = "---\ntitle: x\n---\n%% note\n%%{init: {}}%%\n\ngraph TD\n  a --> b"
    out = set_direction(code, "RL")
    assert out.splitlines()[6] == "graph RL"
    assert out.startswith("---\ntitle: x\n---\n%% note\n%%{init: {}}%%\n")


def test_set_direction_keeps_header_suffix():
    assert set_direction("graph TD;\n  a-->b", "BT") == "graph BT;\n  a-->b"


@pytest.mark.parametrize("kind", ["stateDiagram", "stateDiagram-v2", "classDiagram"])
def test_set_direction_adds_statement(kind):
    code = f"{kind}\n  A --> B"
    assert set_direction(code, "LR") == f"{kind}\n  direction LR\n  A --> B"


def test_set_direction_replaces_top_level_statement_only():
    code = (
        "stateDiagram-v2\n"
        "  state Outer {\n"
        "    direction LR\n"
        "    a --> b\n"
        "  }\n"
        "  direction TB\n"
        "  [*] --> Outer"
    )
    out = set_direction(code, "RL")
    assert "    direction LR\n" in out
    assert "  direction RL\n" in out
    assert "direction TB" not in out


def test_set_direction_statement_writes_td_as_tb():
    assert set_direction("classDiagram\n  direction LR\n  A <|-- B", "TD") == (
        "classDiagram\n  direction TB\n  A <|-- B"
    )


@pytest.mark.parametrize(
    "code,direction,expected",
    [
        ("gitGraph\n  commit", "LR", "gitGraph LR:\n  commit"),
        ("gitGraph LR:\n  commit", "TD", "gitGraph TB:\n  commit"),
        ("gitGraph TB:\n  commit", "BT", "gitGraph BT:\n  commit"),
        ("gitGraph LR:\n  commit", "RL", "gitGraph LR:\n  commit"),
    ],
)
def test_set_direction_gitgraph(code, direction, expected):
    assert set_direction(code, direction) == expected


@pytest.mark.parametrize(
    "code", ["erDiagram\n  A ||--o{ B : has", 'pie\n  "a": 1', "", "%% only"]
)
def test_set_direction_unsupported_unchanged(code):
    assert set_direction(code, "LR") == code


FRONTMATTER = """\
---
title: Demo
config:
  theme: forest
  themeVariables:
    primaryColor: "#fff"
---
flowchart TD
  a --> b
"""


def test_code_theme_reads_frontmatter():
    assert code_theme(FRONTMATTER) == "forest"


@pytest.mark.parametrize(
    "code",
    [
        "flowchart TD\n  a --> b",
        "---\ntitle: Demo\n---\nflowchart TD",
        "---\nconfig:\n  look: handDrawn\n---\nflowchart TD",
        "---\ntheme: dark\n---\nflowchart TD",
        "---\nconfig:\n  flowchart:\n    theme: dark\n---\nflowchart TD",
        "flowchart TD\n  theme: dark",
        "---\nconfig:\n  themeVariables:\n    x: 1\n---\nflowchart TD",
    ],
)
def test_code_theme_none(code):
    assert code_theme(code) is None


def test_code_theme_quoted_and_leading_blank_lines():
    assert code_theme("\n---\nconfig:\n    theme: 'dark'\n---\nflowchart TD") == "dark"
