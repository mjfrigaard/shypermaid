import pytest
from playwright.sync_api import Page, expect
from shiny.pytest import create_app_fixture

app = create_app_fixture("e2e_app.py")

TEXTAREA = ".sm-code textarea"


@pytest.fixture
def editor(page: Page, app) -> Page:
    page.goto(app.url)
    page.wait_for_selector(".sm-stage svg")
    page.locator(TEXTAREA).fill("flowchart TD")
    page.locator(TEXTAREA).press("End")
    return page


def code(page: Page) -> str:
    return page.locator(TEXTAREA).input_value()


def test_tab_inserts_spaces(editor: Page):
    editor.keyboard.press("Tab")
    assert code(editor) == "flowchart TD    "
    expect(editor.locator(TEXTAREA)).to_be_focused()


def test_shift_tab_stays_in_editor(editor: Page):
    editor.keyboard.press("Shift+Tab")
    expect(editor.locator(TEXTAREA)).to_be_focused()


def test_escape_then_tab_leaves_editor(editor: Page):
    editor.keyboard.press("Escape")
    editor.keyboard.press("Tab")
    assert code(editor) == "flowchart TD"
    expect(editor.locator(TEXTAREA)).not_to_be_focused()


def test_escape_then_shift_tab_leaves_editor(editor: Page):
    editor.keyboard.press("Escape")
    editor.keyboard.press("Shift+Tab")
    assert code(editor) == "flowchart TD"
    expect(editor.locator(TEXTAREA)).not_to_be_focused()


def test_typing_after_escape_traps_tab_again(editor: Page):
    editor.keyboard.press("Escape")
    editor.keyboard.type("x")
    editor.keyboard.press("Tab")
    assert code(editor) == "flowchart TDx    "
    expect(editor.locator(TEXTAREA)).to_be_focused()


def test_release_resets_on_refocus(editor: Page):
    editor.keyboard.press("Escape")
    editor.keyboard.press("Tab")
    editor.locator(TEXTAREA).focus()
    editor.keyboard.press("Tab")
    assert code(editor) == "flowchart TD    "


def test_hint_describes_textarea(editor: Page):
    hint = editor.locator(".sm-key-hint")
    expect(hint).to_contain_text("Press Escape, then Tab")
    hint_id = hint.get_attribute("id")
    expect(editor.locator(TEXTAREA)).to_have_attribute("aria-describedby", hint_id)
