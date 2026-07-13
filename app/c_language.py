"""C LanguageProvider: syntax highlighting and compile+run execution for Gloat IDE.

Supports a "Compiler:" toolbar picker (gcc/clang), reusing the same
registry-of-backends pattern as BLADE's BasicBackend, since both compilers
are already commonly installed and adding a second one is essentially free.
"""

from __future__ import annotations

import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from PyQt6.QtCore import QProcess, QSettings
from PyQt6.QtGui import QTextDocument
from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QWidget

from app.language import LanguageProvider
from app.syntax import BlockCommentHighlighter, HighlightRule, keyword_rule
from app.themes import SyntaxColors

C_KEYWORDS = [
    "auto", "break", "case", "char", "const", "continue", "default", "do",
    "double", "else", "enum", "extern", "float", "for", "goto", "if", "inline",
    "int", "long", "register", "restrict", "return", "short", "signed",
    "sizeof", "static", "struct", "switch", "typedef", "union", "unsigned",
    "void", "volatile", "while", "_Bool", "_Complex", "_Imaginary",
]

C_BUILTINS = [
    "printf", "scanf", "fprintf", "fscanf", "sprintf", "sscanf", "malloc",
    "calloc", "realloc", "free", "strlen", "strcpy", "strncpy", "strcmp",
    "strcat", "memcpy", "memset", "memmove", "fopen", "fclose", "fread",
    "fwrite", "exit", "abs", "pow", "sqrt",
]


def _c_rules() -> List[HighlightRule]:
    return [
        HighlightRule(re.compile(r"^\s*#\s*\w+.*"), "builtin"),
        keyword_rule(C_KEYWORDS, "keyword"),
        keyword_rule(C_BUILTINS, "builtin"),
        HighlightRule(re.compile(r"\b0[xX][0-9a-fA-F]+\b"), "number"),
        HighlightRule(re.compile(r"\b\d+\.?\d*[fFlLuU]?\b"), "number"),
        HighlightRule(re.compile(r"'(?:\\.|[^'\\])'"), "string"),
        HighlightRule(re.compile(r'"(?:\\.|[^"\\])*"'), "string"),
        HighlightRule(re.compile(r"//.*"), "comment"),
    ]


class CHighlighter(BlockCommentHighlighter):
    def __init__(self, document: QTextDocument, syntax_colors: SyntaxColors):
        super().__init__(document, syntax_colors, _c_rules(), r"/\*", r"\*/")


@dataclass(frozen=True)
class CCompiler:
    key: str
    label: str
    command: str


COMPILERS: Dict[str, CCompiler] = {
    "gcc": CCompiler(key="gcc", label="GCC", command="gcc"),
    "clang": CCompiler(key="clang", label="Clang", command="clang"),
}

DEFAULT_COMPILER = "gcc"


class CLanguageProvider(LanguageProvider):
    """Compiles C source with a selectable compiler, then runs the resulting binary."""

    def __init__(self):
        self._settings = QSettings("GloatIDE", "Gloat IDE")
        saved = self._settings.value("c/compiler", DEFAULT_COMPILER)
        self._compiler_key = saved if saved in COMPILERS else DEFAULT_COMPILER
        self._process: Optional[QProcess] = None
        self._source_path: Optional[Path] = None
        self._exe_path: Optional[Path] = None

    @property
    def name(self) -> str:
        return "C"

    @property
    def file_extensions(self) -> List[str]:
        return [".c", ".h"]

    def create_highlighter(self, document: QTextDocument, syntax_colors: SyntaxColors) -> CHighlighter:
        return CHighlighter(document, syntax_colors)

    def create_toolbar_widget(self, parent: QWidget) -> QWidget:
        container = QWidget(parent)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(QLabel("Compiler:"))

        combo = QComboBox(container)
        for compiler in COMPILERS.values():
            combo.addItem(compiler.label, compiler.key)
        index = combo.findData(self._compiler_key)
        combo.setCurrentIndex(index if index >= 0 else 0)
        combo.currentIndexChanged.connect(lambda idx: self._set_compiler(combo.itemData(idx)))
        layout.addWidget(combo)
        return container

    def _set_compiler(self, key: str) -> None:
        if key in COMPILERS:
            self._compiler_key = key
            self._settings.setValue("c/compiler", key)

    def run(self, source: str, terminal) -> None:
        self._stop_process()
        compiler = COMPILERS[self._compiler_key]

        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False, encoding="utf-8")
        tmp.write(source)
        tmp.close()
        self._source_path = Path(tmp.name)
        self._exe_path = self._source_path.with_suffix("")

        gcc_process = QProcess()
        gcc_process.setProgram(compiler.command)
        gcc_process.setArguments([str(self._source_path), "-o", str(self._exe_path), "-lm"])
        gcc_process.readyReadStandardOutput.connect(lambda: self._forward_output(gcc_process, terminal))
        gcc_process.readyReadStandardError.connect(lambda: self._forward_error(gcc_process, terminal))
        gcc_process.errorOccurred.connect(lambda _err: terminal.write(f"[error] {gcc_process.errorString()}"))
        gcc_process.finished.connect(lambda code, _status: self._on_compile_finished(code, terminal))
        self._process = gcc_process
        gcc_process.start()

    def _on_compile_finished(self, exit_code: int, terminal) -> None:
        if exit_code != 0 or self._exe_path is None or not self._exe_path.exists():
            terminal.write(f"\n[Compile failed with code {exit_code}]")
            self._cleanup_files()
            self._process = None
            return

        process = QProcess()
        process.setProgram(str(self._exe_path))
        process.readyReadStandardOutput.connect(lambda: self._forward_output(process, terminal))
        process.readyReadStandardError.connect(lambda: self._forward_error(process, terminal))
        process.finished.connect(lambda code, _status: self._on_run_finished(code, terminal))
        process.errorOccurred.connect(lambda _err: terminal.write(f"[error] {process.errorString()}"))
        self._process = process
        process.start()

    def handle_input(self, text: str, terminal) -> None:
        if self._process is not None and self._process.state() == QProcess.ProcessState.Running:
            self._process.write((text + "\n").encode("utf-8"))
        else:
            terminal.write("[No running process to receive input]")

    def _forward_output(self, process: QProcess, terminal) -> None:
        data = bytes(process.readAllStandardOutput().data())
        if data:
            terminal.write(data.decode("utf-8", errors="replace").rstrip("\n"))

    def _forward_error(self, process: QProcess, terminal) -> None:
        data = bytes(process.readAllStandardError().data())
        if data:
            terminal.write(data.decode("utf-8", errors="replace").rstrip("\n"))

    def _on_run_finished(self, exit_code: int, terminal) -> None:
        terminal.write(f"\n[Process exited with code {exit_code}]")
        self._cleanup_files()
        self._process = None

    def _stop_process(self) -> None:
        if self._process is not None:
            self._process.kill()
            self._process.waitForFinished(1000)
            self._process = None
        self._cleanup_files()

    def _cleanup_files(self) -> None:
        if self._source_path is not None and self._source_path.exists():
            self._source_path.unlink(missing_ok=True)
        self._source_path = None
        if self._exe_path is not None and self._exe_path.exists():
            self._exe_path.unlink(missing_ok=True)
        self._exe_path = None
