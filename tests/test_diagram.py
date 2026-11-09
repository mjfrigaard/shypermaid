import pytest

from shymermaid.diagram import DEFAULT_CODE, render_config, set_direction


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


@pytest.mark.parametrize("theme,look", [("nope", "classic"), ("dark", "nope")])
def test_render_config_invalid(theme, look):
    with pytest.raises(ValueError):
        render_config(theme, look)
