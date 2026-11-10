import pytest
from playwright.sync_api import Page, expect
from shiny.pytest import create_app_fixture

app = create_app_fixture("e2e_app.py")

TEXTAREA = ".sm-code textarea"
LAYER = ".sm-highlight code"


@pytest.fixture
def editor(page: Page, app) -> Page:
    page.goto(app.url)
    page.wait_for_selector(".sm-stage svg")
    return page


def layer_text(page: Page) -> str:
    return page.locator(LAYER).text_content()


def set_code(page: Page, code: str) -> None:
    page.locator(TEXTAREA).fill(code)


def tokens(page: Page, kind: str) -> list[str]:
    return page.locator(f"{LAYER} .sm-tok-{kind}").all_text_contents()


def test_layer_matches_code_on_load(editor: Page):
    assert layer_text(editor) == editor.locator(TEXTAREA).input_value() + "\n "


def test_layer_follows_edits(editor: Page):
    set_code(editor, "flowchart TD\n  a --> b")
    assert layer_text(editor) == "flowchart TD\n  a --> b\n "


@pytest.mark.parametrize(
    "code,kind,expected",
    [
        (
            "flowchart LR\n  subgraph S\n  end",
            "keyword",
            ["flowchart", "subgraph", "end"],
        ),
        ("graph TD", "dir", ["TD"]),
        ('a["one"] --> b("two")', "string", ['"one"', '"two"']),
        (
            "a --> b\nc -.-> d\ne ==> f\nA->>B: hi",
            "arrow",
            ["-->", "-.->", "==>", "->>"],
        ),
        ("a -->|yes| b", "label", ["|yes|"]),
        (
            "%% note\n%%{init: {}}%%\n---",
            "comment",
            ["%% note", "%%{init: {}}%%", "---"],
        ),
    ],
)
def test_token_classes(editor: Page, code: str, kind: str, expected: list[str]):
    set_code(editor, code)
    assert tokens(editor, kind) == expected


def test_comment_hides_other_tokens(editor: Page):
    set_code(editor, '%% a --> "b" flowchart')
    assert tokens(editor, "comment") == ['%% a --> "b" flowchart']
    for kind in ("arrow", "string", "keyword"):
        assert tokens(editor, kind) == []


def test_keyword_needs_word_boundary(editor: Page):
    set_code(editor, "ending --> graphic")
    assert tokens(editor, "keyword") == []


def test_html_is_escaped(editor: Page):
    set_code(editor, 'a["<b>bold</b>"] --> c<img src=x>')
    assert editor.locator(f"{LAYER} b, {LAYER} img").count() == 0
    assert layer_text(editor) == 'a["<b>bold</b>"] --> c<img src=x>\n '


def test_trailing_newline_keeps_last_line(editor: Page):
    set_code(editor, "graph TD\n")
    assert layer_text(editor).endswith("\n\n ")


def test_tab_inserts_spaces_and_updates_layer(editor: Page):
    set_code(editor, "graph TD")
    editor.locator(TEXTAREA).press("End")
    editor.locator(TEXTAREA).press("Tab")
    assert editor.locator(TEXTAREA).input_value() == "graph TD    "
    assert layer_text(editor) == "graph TD    \n "


def test_textarea_text_stays_transparent_when_focused(editor: Page):
    editor.locator(TEXTAREA).focus()
    expect(editor.locator(TEXTAREA)).to_have_css("color", "rgba(0, 0, 0, 0)")


def test_layers_share_box_and_font(editor: Page):
    diff = editor.evaluate(
        """() => {
          const t = document.querySelector('.sm-code textarea');
          const p = document.querySelector('.sm-highlight');
          const keys = ['fontFamily', 'fontSize', 'lineHeight', 'letterSpacing',
                        'paddingTop', 'paddingLeft', 'tabSize', 'whiteSpace'];
          const a = t.getBoundingClientRect(), b = p.getBoundingClientRect();
          const box = ['x', 'y', 'width', 'height'].filter(k => a[k] !== b[k]);
          return keys.filter(k => getComputedStyle(t)[k] !== getComputedStyle(p)[k])
            .concat(box);
        }"""
    )
    assert diff == []


@pytest.mark.parametrize("top,left", [(400, 120), (10**6, 10**6)])
def test_scroll_sync(editor: Page, top: int, left: int):
    set_code(editor, "\n".join(f"    node_{i} --> node_{i + 1}" * 3 for i in range(80)))
    pos = editor.evaluate(
        """([top, left]) => new Promise(done => {
          const t = document.querySelector('.sm-code textarea');
          const p = document.querySelector('.sm-highlight');
          t.scrollTop = top;
          t.scrollLeft = left;
          requestAnimationFrame(() => done(
            [t.scrollTop, t.scrollLeft, p.scrollTop, p.scrollLeft]));
        })""",
        [top, left],
    )
    assert pos[0] > 0 and pos[1] > 0
    assert pos[:2] == pos[2:]
