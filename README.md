# shymermaid

A Shiny for Python (Core) app-package that renders Mermaid diagrams. Write Mermaid code in the left pane and the diagram updates on the canvas to the right.

## Features

- Code editor in a collapsible sidebar, with an Auto-Update switch and a Render button
- Theme (default, neutral, dark, forest, base), look (classic, hand drawn), and direction (as written, TD, BT, LR, RL) menus
- Pan and zoom, 1:1, fit to screen, fullscreen, and SVG download
- Parse errors show on the canvas while the last good diagram stays in place

## Install

Using `uv`:

```bash
uv venv
uv pip install -e ".[dev]"
```

Using `venv`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run

```bash
uv run shymermaid
```

Or with autoreload during development:

```bash
uv run shiny run shymermaid.app:app --reload
```

From Python:

```python
from shymermaid import run_app

run_app(port=8000)
```

The app loads Mermaid and svg-pan-zoom from jsdelivr, so it needs an internet connection.

## Use the modules in another app

```python
from shiny import App, ui

from shymermaid import editor_server, editor_ui, viewer_server, viewer_ui

app_ui = ui.page_fillable(
    ui.layout_sidebar(ui.sidebar(editor_ui("editor")), viewer_ui("viewer"))
)


def server(input, output, session):
    code = editor_server("editor")
    viewer_server("viewer", code=code)


app = App(app_ui, server)
```

The page also needs the Mermaid, svg-pan-zoom, and `www/` assets that `shymermaid.app.app_ui()` adds to the page head.

## Develop

```bash
uv run pytest
uv run ruff check src tests
uv run mypy src
```

## Layout

```
src/shymermaid/
├── __init__.py
├── diagram.py      # Shiny free helpers: set_direction(), render_config()
├── modules.py      # editor and viewer modules
├── app.py          # app_ui(), server(), create_app(), run_app()
└── www/
    ├── mermaid-binding.js
    └── styles.css
tests/
├── test_app.py
└── test_diagram.py
```
