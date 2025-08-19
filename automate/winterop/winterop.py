from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from typing import TYPE_CHECKING, cast

from cffi import FFI

if TYPE_CHECKING:
    from typing import Protocol

    class Winterop(Protocol):
        def outline(
            self,
            left: int,
            top: int,
            right: int,
            bottom: int,
            thickness: int,
            color: int,
            duration_ms: int,
        ) -> None: ...

        def fast_outline(
            self,
            left: int,
            top: int,
            right: int,
            bottom: int,
            thickness: int,
            color: int,
        ) -> None: ...

        def type_text(self, text: bytes, delay_ms: int) -> bool: ...
        def click_mouse(self, x: int, y: int) -> bool: ...


def get_project_root() -> Path:
    marker_files = ("pyproject.toml", "setup.py", ".git")
    path = Path(__file__).resolve()
    for parent in [path] + list(path.parents):
        if any((parent / mf).exists() for mf in marker_files):
            return parent
    return path.parent


ROOT = get_project_root()
MODULE_NAME = "_winterop"
BUILD_DIR = ROOT / "build/"
CACHE_FILE = BUILD_DIR / f"{MODULE_NAME}.build"
BUILD_DIR.mkdir(exist_ok=True)

SOURCE = Path(__file__).parent / "winterop.c"
HEADER = SOURCE.with_name("winterop.h")

sys.path.append(str(BUILD_DIR))


def ensure_extension() -> None:
    src = SOURCE.read_text()
    src_hash = hashlib.sha256(src.encode()).hexdigest()

    if CACHE_FILE.exists() and CACHE_FILE.read_text() == src_hash:
        return

    ffi = FFI()
    ffi.cdef(HEADER.read_text())
    ffi.set_source(
        MODULE_NAME,
        src,
        libraries=["user32", "gdi32", "kernel32"],
    )
    Path(ffi.compile(tmpdir=str(BUILD_DIR), verbose=True))

    CACHE_FILE.write_text(src_hash)


ensure_extension()

import _winterop

_lib = _winterop.lib = cast("Winterop", _winterop.lib)


def outline(
    left: int,
    top: int,
    right: int,
    bottom: int,
    thickness: int,
    color: int,
    duration_ms: int,
) -> None:
    return _lib.outline(left, top, right, bottom, thickness, color, duration_ms)


def fast_outline(
    left: int,
    top: int,
    right: int,
    bottom: int,
    thickness: int,
    color: int,
) -> None:
    return _lib.fast_outline(left, top, right, bottom, thickness, color)


def type_text(text: str, delay_ms: int) -> bool:
    text_b = text.encode("utf-8")
    return bool(_lib.type_text(text_b, delay_ms))


def click_mouse(x: int, y: int) -> bool:
    return bool(_lib.click_mouse(x, y))
