"""Write the source of the downloadable Italian book, pdf_book_it.qmd.

The PDF exists for the Italian translation only: the Greek edition and Long's
English are already published elsewhere, and what this project adds is the
Italian.

The completed Italian text is read from translation/it. The preceding validation
step in run.bat guarantees that every title and numbered section is present.
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import translation_store
from site_config import LANGS, PDF_FILENAME, ROMAN, ROOT

LANG = 'it'
OUTPUT_QMD = ROOT / 'pdf_book_it.qmd'
DATA = ROOT / 'data'

LATEX_REPLACEMENTS = {
    '\\': r'\textbackslash{}',
    '&': r'\&',
    '%': r'\%',
    '$': r'\$',
    '#': r'\#',
    '_': r'\_',
    '{': r'\{',
    '}': r'\}',
    '~': r'\textasciitilde{}',
    '^': r'\textasciicircum{}',
}


def escape_latex(text):
    return ''.join(LATEX_REPLACEMENTS.get(character, character) for character in text or '')


def markup(text):
    """The same small Markdown subset the site accepts, in LaTeX."""
    out = escape_latex(text)
    # The underscores of _corsivo_ have just been escaped; match them as such.
    out = re.sub(r'(?<!\w)\\_([^\n]+?)\\_(?!\w)', r'\\textit{\1}', out)
    out = re.sub(r'\*\*([^*]+)\*\*', r'\\textbf{\1}', out)
    out = re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+)\)', r'\1 (\\url{\2})', out)
    out = re.sub(r'`([^`]+)`', r'\\texttt{\1}', out)
    return out


def paragraphs_of(text):
    return [
        ' '.join(line.strip() for line in block.splitlines() if line.strip())
        for block in re.split(r'\n\s*\n', text.strip())
        if block.strip()
    ]


def load_json(name):
    return json.loads((DATA / name).read_text(encoding='utf-8'))


def render_front_matter(intro):
    parts = []
    for paragraph in intro.get(LANG, []):
        if paragraph.strip().upper().startswith('TODO'):
            # Placeholders belong in the working files, never in the book.
            continue
        parts += [markup(paragraph), '', r'\vspace{0.2em}', '']
    parts += [r'\clearpage', '']
    return parts


def render_section(number, text):
    # A plain space after the number, not a tilde: Pandoc would print the tilde.
    body = paragraphs_of(text)
    lines = [f'\\textbf{{{number}}} {markup(body[0])}']
    for extra in body[1:]:
        lines += [r'\par', markup(extra)]
    lines.append('')
    return lines


def render_gap(numbers):
    """One line standing for a run of sections still to be translated."""
    label = str(numbers[0]) if len(numbers) == 1 else f'{numbers[0]}--{numbers[-1]}'
    return [f'\\textbf{{{label}}} […]', '']


def render_diatribe(diatribe, entry):
    ui = LANGS[LANG]['ui']
    title = entry['title'] or diatribe['title']['en']
    reference = f'{ROMAN[diatribe["book"]]}.{diatribe["chapter"]}'
    parts = [f'## {escape_latex(ui["diatribe"] + " " + reference + " — " + title)}', '']
    pending = 0
    gap = []
    for section in diatribe['sections']:
        text = entry['sections'].get(section['n'], '')
        if not text:
            pending += 1
            gap.append(section['n'])
            continue
        if gap:
            parts += render_gap(gap)
            gap = []
        parts += render_section(section['n'], text)
    if gap:
        parts += render_gap(gap)
    if pending:
        parts += [
            r'\begingroup\small\itshape',
            f'({pending} '
            f'{"sezione non ancora tradotta" if pending == 1 else "sezioni non ancora tradotte"}: '
            'il testo completo è sul sito.)',
            r'\endgroup',
            '',
        ]
    return parts


def render_credits(credits):
    parts = [r'\clearpage', f'# {escape_latex(LANGS[LANG]["ui"]["credits"])}', '']
    for paragraph in credits.get(LANG, []):
        parts += [markup(paragraph), '']
    return parts


def build(diatribes, translations, intro, credits):
    cfg = LANGS[LANG]
    parts = [
        '<!--',
        'FILE GENERATO. NON MODIFICARE A MANO.',
        '',
        'Modificare invece:',
        '- translation/it/**.md   per il testo tradotto',
        '- data/intro.json        per la nota introduttiva',
        '- data/credits.json      per fonti e crediti',
        '- pdf/pdf-preamble.tex   per l\'impaginazione',
        '',
        'Poi eseguire:',
        '    run.bat',
        '-->',
        '',
        '---',
        f'output-file: "{PDF_FILENAME.removesuffix(".pdf")}"',
        'lang: it',
        'format:',
        '  pdf:',
        '    documentclass: scrartcl',
        '    pdf-engine: xelatex',
        '    papersize: a5',
        '    fontsize: 10.5pt',
        '    toc: true',
        '    toc-depth: 2',
        '    number-sections: false',
        '    colorlinks: true',
        # The names come from pdf/pdf-preamble.tex, which xcolor has by then.
        '    linkcolor: eptealdark',
        '    urlcolor: eptealdark',
        '    citecolor: eptealdark',
        '    geometry:',
        '      - top=17mm',
        '      - bottom=22mm',
        '      - inner=18mm',
        '      - outer=16mm',
        '      - footskip=9mm',
        '    include-in-header: pdf/pdf-preamble.tex',
        '    include-before-body: pdf/cover-it.tex',
        '---',
        '',
    ]
    parts += render_front_matter(intro)

    included = 0
    # Book 0 is Arrian's dedicatory letter: it belongs to the site, not to the
    # book, which starts where the diatribes start.
    for book in sorted({diatribe['book'] for diatribe in diatribes} - {0}):
        items = [
            diatribe for diatribe in diatribes
            if diatribe['book'] == book
            and translations.get(diatribe['slug'], {}).get('sections')
        ]
        if not items:
            continue
        parts += [r'\clearpage', f'# {escape_latex(cfg["book_label"](book))}', '']
        for diatribe in items:
            parts += render_diatribe(diatribe, translations[diatribe['slug']])
            included += 1

    parts += render_credits(credits)
    return '\n'.join(parts).rstrip() + '\n', included


def main():
    data = json.loads((DATA / 'discourses.json').read_text(encoding='utf-8'))
    diatribes = data['diatribes']
    translations = translation_store.load_all(diatribes)
    done, total, _ = translation_store.progress(diatribes, translations)

    text, included = build(
        diatribes, translations, load_json('intro.json'), load_json('credits.json')
    )
    if not included:
        if OUTPUT_QMD.exists():
            OUTPUT_QMD.unlink()
        print('PDF: nessuna diatriba ancora tradotta, il libro italiano non viene generato.')
        return 1

    OUTPUT_QMD.write_text(text, encoding='utf-8')
    print(f'Scritto {OUTPUT_QMD.name}: {included} diatribe, '
          f'{done}/{total} sezioni tradotte.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
