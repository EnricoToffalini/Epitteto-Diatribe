"""Idempotent file writing and hashing helpers shared by the build tools.

The generators used to rewrite every output on each run; that reset the mtime of
~900 files and forced Quarto to re-render the whole site.  Writing only when the
content actually changes turns the generated files into a reliable change signal
for tools/5_render.py.
"""

import hashlib
import shutil
from pathlib import Path


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_if_changed(path, text, encoding='utf-8'):
    """Write ``text`` to ``path`` only if it differs from what is already there.

    Returns True when the file was written (new or changed), False otherwise.
    """
    path = Path(path)
    if path.exists():
        try:
            if path.read_text(encoding=encoding) == text:
                return False
        except UnicodeDecodeError:
            pass
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding=encoding)
    return True


def copy_if_changed(src, dst):
    """Copy ``src`` onto ``dst`` only if the bytes differ.  Returns True on copy."""
    src, dst = Path(src), Path(dst)
    if dst.exists() and dst.read_bytes() == src.read_bytes():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    return True
