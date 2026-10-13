"""Render only what changed.

`run.bat` used to run a full `quarto render` (~295 pages, minutes) on every build,
even for a one-line fix to a single diatribe.  The site has no executable code, so
Quarto has no incremental mode of its own; this script adds one.

How it works: the Python generators (steps 0-4 of run.bat) now write their output
files only when the content actually changes, so a SHA-256 of every generated
file is a faithful record of what a change touched.  This script keeps those
hashes in `.render-cache.json` and, on the next run, renders

  * the whole site         if a *global* input changed (theme, navbar/sidebar,
                           shared includes, assets, Quarto version) or the set of
                           pages changed or `--full` was passed;
  * only the changed pages  otherwise (one `quarto render page.qmd` call each,
                           falling back to a full render if any of them fails);
  * nothing                 if no page changed.

The Italian PDF is rendered only when one of its inputs changed.

Usage:  python tools/5_render.py [--full]
        QUARTO_BIN      path to the quarto executable (default: "quarto")
        RENDER_THRESHOLD  above this many changed pages, do a full render (40)
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from site_config import PDF_FILENAME, ROOT
from io_utils import sha256_file

TOOLS = Path(__file__).resolve().parent
CACHE = ROOT / '.render-cache.json'
CACHE_VERSION = 1
QUARTO_BIN = os.environ.get('QUARTO_BIN') or 'quarto'
THRESHOLD = int(os.environ.get('RENDER_THRESHOLD', '40'))
DOCS = ROOT / 'docs'

# Hand-authored or generated files that every page embeds: a change to any of
# them invalidates the whole site.
GLOBAL_FILES = [
    '_quarto.yml',
    'styles.css',
    'site-head.html',
    'lang-config.html',
    'lang-switch.html',
    'it/seo-head.html',
    'en/seo-head.html',
    'grc/seo-head.html',
]

PDF_FILES = [
    'pdf_book_it.qmd',
    'pdf/pdf-preamble.tex',
    'pdf/cover-it.tex',
    'data/cover.png',
]


def rel(path):
    return path.relative_to(ROOT).as_posix()


def hash_files(relatives):
    return {r: sha256_file(ROOT / r) for r in relatives if (ROOT / r).exists()}


def global_inputs():
    relatives = list(GLOBAL_FILES)
    relatives += sorted(rel(p) for p in (ROOT / 'assets').rglob('*') if p.is_file())
    return hash_files(relatives)


def page_inputs():
    pages = ['index.qmd']
    for lang in ('it', 'en', 'grc'):
        pages += sorted(rel(p) for p in (ROOT / lang).rglob('*.qmd'))
    return hash_files(pages)


def quarto_version():
    out = subprocess.run(
        [QUARTO_BIN, '--version'], capture_output=True, text=True, check=True
    )
    return out.stdout.strip().splitlines()[0].strip()


def load_cache():
    if not CACHE.exists():
        return None
    try:
        data = json.loads(CACHE.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return None
    return data if data.get('version') == CACHE_VERSION else None


def quarto(*args):
    subprocess.run([QUARTO_BIN, *args], check=True, cwd=ROOT)


def prune_orphan_html(page_hashes):
    """Delete docs/<lang>/**/*.html with no matching source page."""
    expected = {r[:-len('.qmd')] + '.html' for r in page_hashes}
    removed = 0
    for lang in ('it', 'en', 'grc'):
        for html in (DOCS / lang).rglob('*.html'):
            if html.relative_to(DOCS).as_posix() not in expected:
                html.unlink()
                removed += 1
    if removed:
        print(f'  rimossi {removed} file HTML orfani da docs/')


def finalize_seo():
    subprocess.run([sys.executable, str(TOOLS / '4_finalize_seo.py')],
                   check=True, cwd=ROOT)


def render_pdf():
    if not (ROOT / 'pdf_book_it.qmd').exists():
        print('PDF: pdf_book_it.qmd assente, salto.')
        return
    print('PDF: render di pdf_book_it.qmd...')
    quarto('render', 'pdf_book_it.qmd', '--to', 'pdf')
    # When a single file is not part of the web project some Quarto versions
    # write next to the source instead of into docs/.
    stray = ROOT / PDF_FILENAME
    target = DOCS / PDF_FILENAME
    if stray.exists():
        shutil.move(str(stray), str(target))
    if not target.exists():
        raise SystemExit(f'ERRORE: il PDF non e stato scritto in {target}.')


def main(argv):
    full_flag = '--full' in argv

    version = quarto_version()
    global_now = global_inputs()
    pages_now = page_inputs()
    pdf_now = hash_files(PDF_FILES)
    cache = load_cache()

    full = (
        full_flag
        or cache is None
        or cache.get('quarto') != version
        or cache.get('global') != global_now
        or set(cache.get('pages', {})) != set(pages_now)
    )

    changed_pages = []
    if not full:
        old_pages = cache.get('pages', {})
        changed_pages = sorted(
            p for p, h in pages_now.items() if old_pages.get(p) != h
        )
        if len(changed_pages) > THRESHOLD:
            print(f'{len(changed_pages)} pagine cambiate (> {THRESHOLD}): '
                  'render completo.')
            full = True

    if full:
        reason = 'forzato con --full' if full_flag else (
            'prima esecuzione' if cache is None else 'input globali cambiati')
        print(f'Render completo del sito ({reason})...')
        prune_orphan_html(pages_now)
        quarto('render')
    elif changed_pages:
        print(f'Render incrementale: {len(changed_pages)} pagina/e')
        for p in changed_pages:
            print(f'  - {p}')
        # One file per call: with several files Quarto renders only the first
        # and hands the others to pandoc as extra inputs.
        try:
            for p in changed_pages:
                quarto('render', p)
            finalize_seo()
        except subprocess.CalledProcessError:
            # A failed partial render can leave docs/ inconsistent: rebuild it all.
            print('Render incrementale fallito: passo al render completo...')
            prune_orphan_html(pages_now)
            quarto('render')
    else:
        print('Nessuna pagina modificata: render del sito saltato.')

    if full_flag or cache is None or cache.get('pdf') != pdf_now:
        render_pdf()
    else:
        print('PDF: nessun input cambiato, salto.')

    new_cache = {
        'version': CACHE_VERSION,
        'quarto': version,
        'global': global_now,
        'pages': pages_now,
        'pdf': pdf_now,
    }
    CACHE.write_text(json.dumps(new_cache, indent=1), encoding='utf-8')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
