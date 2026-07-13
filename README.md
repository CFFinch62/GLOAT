# Gloat IDE

![Gloat IDE banner](gloat_banner.svg)

A lightweight PyQt6 IDE for C, built on the Base IDE skeleton.

## Features
- Top menu bar (File, Edit, View, Theme)
- Toolbar, including a **Compiler** picker (GCC / Clang)
- Left file browser with navigation controls and bookmarks
- Tabbed editor area with line numbers, current-line highlight, and C syntax highlighting
  (including correctly-tracked multi-line `/* ... */` block comments)
- Find/Replace dialog (Ctrl+F)
- Console/terminal panel that compiles with the selected compiler and runs the resulting
  binary, with an input line wired to the running process's stdin
- Status bar with cursor position
- Generic open/save workflow with error dialogs on failure
- Window size, splitter layout, theme, and chosen compiler persisted across restarts

## Requirements
At least one C compiler on `PATH`: `gcc` and/or `clang` (both commonly preinstalled
on Linux; `sudo apt install gcc` / `sudo apt install clang` otherwise).

## Run
```bash
cd "/home/chuck/Dropbox/Programming/Languages_and_Code/Programming_Projects/Programming_Tools/IDES/IDE_Suite 2/GLOAT"
./run.sh
```
`run.sh` creates `venv/` and installs requirements automatically (via
`setup.sh`) on first run, then launches the app. Run `./setup.sh` directly
if you just want to (re)provision the environment without launching.

## Build a standalone binary
```bash
source venv/bin/activate
python build.py
```
Produces a self-contained app in `dist/GLOAT/` via PyInstaller (see `build.py`
and the generated `GLOAT.spec`). Note this only bundles the IDE itself — the
end user still needs a C compiler installed and on `PATH`.

## C support
`app/c_language.py`'s `CLanguageProvider`:
- `create_highlighter` — `CHighlighter` subclasses the shared `BlockCommentHighlighter`
  (see `app/syntax.py`) for keywords, builtins, preprocessor directives, string/char
  literals, numbers (incl. hex), `//` line comments, and properly multi-line `/* */`
  block comments.
- `create_toolbar_widget` — adds the "Compiler:" combo box (GCC/Clang); the choice is
  persisted via `QSettings`.
- `run` — writes the editor's contents to a temp `.c` file, compiles it with the
  selected compiler to a temp binary, then runs that binary via `QProcess`, streaming
  stdout/stderr live. `handle_input` forwards console input to the running process's
  stdin, so `scanf` works interactively.

## Other extension points
- Expand the file browser with project management features such as new folders, rename, and delete.
- Add a preferences dialog for editor font size, tab width, etc.

## License
MIT — see [LICENSE](LICENSE).
