"""Generate the trilingual Quarto site for Epictetus' Discourses.

Each edition gets its own subtree, with the same page at the same relative path:

    it/index.qmd   it/credits.qmd   it/diatribe/1-01.qmd ...
    en/index.qmd   en/credits.qmd   en/diatribe/1-01.qmd ...
    grc/index.qmd  grc/credits.qmd  grc/diatribe/1-01.qmd ...

plus an indexable root index.qmd that offers the three languages.  One
`quarto render` builds all of it.

The three editions differ in what they can show, and the generator follows the
sources rather than pretending they are alike:

  * grc  the Greek text, in the numbered sections every edition cites;
  * it   the completed Italian translation, section by section against the same
         numbers;
  * en   Long's translation as he paragraphed it, with his footnotes.

Everything the reader sees in the interface comes from tools/site_config.py.
"""

from collections import defaultdict
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import translation_store
from io_utils import copy_if_changed, write_if_changed
from site_config import (
    DEFAULT_LANG, DIATRIBE_DIR, GENERATED_FILE_NOTE, GOATCOUNTER,
    GOOGLE_SITE_VERIFICATION, IT_PENDING_ALL, IT_PENDING_SOME, IT_PENDING_TITLE, LANGS,
    LANG_ORDER, PDF_FILENAME, PDF_LANG, ROMAN, ROOT, ROOT_HOME_DESCRIPTION,
    ROOT_HOME_TITLE, SITE_BRAND, SITE_URL, diatribe_path,
    greek_numeral, pages_list,
)

DATA = ROOT / 'data'
ASSETS = ROOT / 'assets'


# ---------------------------------------------------------------------------
# Small text helpers
# ---------------------------------------------------------------------------

def esc(text):
    return html.escape(text or '', quote=True)


def inline_markup(text):
    """The deliberately small Markdown subset allowed in the JSON prose files."""
    out = esc(text)
    out = re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+)\)', r'<a href="\2">\1</a>', out)
    out = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', out)
    out = re.sub(r'(?<!\w)_([^_\n]+)_(?!\w)', r'<i>\1</i>', out)
    out = re.sub(r'`([^`]+)`', r'<code>\1</code>', out)
    return out


def one_block(fragment):
    """Keep generated HTML free of blank lines.

    Pandoc ends a raw HTML block at the first blank line and starts reading
    Markdown again, which would break a page open in the middle.
    """
    return re.sub(r'\n\s*\n', '\n', fragment).strip()


def yaml_value(value):
    return json.dumps(value, ensure_ascii=False)


def load_json(name):
    return json.loads((DATA / name).read_text(encoding='utf-8'))


def prose(source, lang, css_class):
    """Paragraphs from intro.json / credits.json, with TODO shown as a placeholder."""
    paragraphs = source.get(lang)
    if not isinstance(paragraphs, list) or not paragraphs:
        raise SystemExit(f'Missing prose for "{lang}" in the data files.')
    out = [f'<div class="{css_class}">']
    for paragraph in paragraphs:
        text = paragraph.strip()
        if text.upper().startswith('TODO'):
            body = inline_markup(text.split(':', 1)[-1].strip())
            out.append(f'<p class="todo"><span class="todo-tag">DA SCRIVERE</span> {body}</p>')
        else:
            out.append(f'<p>{inline_markup(text)}</p>')
    out.append('</div>')
    return one_block('\n'.join(out))


# ---------------------------------------------------------------------------
# Naming
# ---------------------------------------------------------------------------

def diatribe_number(lang, value, book=False):
    return greek_numeral(value, upper=book) if lang == 'grc' else str(value)


def diatribe_reference(lang, diatribe):
    """The "I.1" that identifies a diatribe, in the style of its edition."""
    book, chapter = diatribe['book'], diatribe['chapter']
    if lang == 'grc':
        return f'{greek_numeral(book, upper=True)}.{greek_numeral(chapter)}'
    return f'{ROMAN[book]}.{chapter}'


def page_label(lang, diatribe):
    """"Diatriba I.1", "Discourse I.1", "Διατριβὴ Αʹ.αʹ", or Arrian's letter."""
    ui = LANGS[lang]['ui']
    if diatribe['book'] == 0:
        return ui['letter']
    return f'{ui["diatribe_at"]} {diatribe_reference(lang, diatribe)}'


def menu_label(lang, diatribe, title):
    if diatribe['book'] == 0:
        return LANGS[lang]['ui']['letter']
    return f'{diatribe_number(lang, diatribe["chapter"])} · {title}'


def title_for(lang, diatribe, translations):
    """(title, is_fallback) for a diatribe in one language."""
    if lang == 'grc':
        return diatribe['title']['grc'], False
    if lang == 'en':
        return diatribe['title']['en'], False
    italian = translations.get(diatribe['slug'], {}).get('title', '')
    if italian:
        return italian, False
    return diatribe['title']['en'], True


def translated_sections(diatribe, translations):
    return translations.get(diatribe['slug'], {}).get('sections', {})


# ---------------------------------------------------------------------------
# _quarto.yml
# ---------------------------------------------------------------------------

def language_span(lang):
    """Label for a language link, tagged for styles.css and lang-switch.html."""
    return f'[{LANGS[lang]["label"]}]{{.ep-lang data-lang="{lang}"}}'


def books_of(diatribes):
    books = defaultdict(list)
    for diatribe in diatribes:
        books[diatribe['book']].append(diatribe)
    return dict(sorted(books.items()))


def write_quarto_yml(diatribes, translations):
    books = books_of(diatribes)
    nav_lang = DEFAULT_LANG  # relabelled client-side by lang-switch.html

    def entry(lang, diatribe, indent):
        pad = ' ' * indent
        title = title_for(lang, diatribe, translations)[0]
        return (f'{pad}- text: {yaml_value(menu_label(lang, diatribe, title))}\n'
                f'{pad}  href: {lang}/{diatribe_path(diatribe["slug"])}.qmd')

    # Navbar: the letter, then one dropdown per book, then the credits page.
    navbar = []
    letter = books[0][0]
    navbar.append(f'      - text: {yaml_value(LANGS[nav_lang]["ui"]["letter"])}\n'
                  f'        href: {nav_lang}/{diatribe_path(letter["slug"])}.qmd')
    for book, items in books.items():
        if book == 0:
            continue
        entries = '\n'.join(entry(nav_lang, item, 10) for item in items)
        navbar.append(f'      - text: {yaml_value(LANGS[nav_lang]["book_label"](book))}\n'
                      f'        menu:\n{entries}')
    navbar.append(f'      - text: {yaml_value(LANGS[nav_lang]["ui"]["credits"])}\n'
                  f'        href: {nav_lang}/credits.qmd')

    flags = '\n'.join(
        f"      - text: '{language_span(lang)}'\n"
        f'        href: {lang}/index.qmd'
        for lang in LANG_ORDER
    )

    sidebars = []
    for lang in LANG_ORDER:
        ui = LANGS[lang]['ui']
        languages = '\n'.join(
            f"        - text: '{language_span(other)}'\n"
            f'          href: {other}/index.qmd'
            for other in LANG_ORDER
        )
        sections = []
        for book, items in books.items():
            if book == 0:
                continue
            entries = '\n'.join(entry(lang, item, 12) for item in items)
            sections.append(f'        - section: {yaml_value(LANGS[lang]["book_label"](book))}\n'
                            f'          contents:\n{entries}')
        sidebars.append(f'''    - id: {lang}
      style: docked
      collapse-level: 1
      contents:
{languages}
        - text: "---"
        - text: {yaml_value(ui['home'])}
          href: {lang}/index.qmd
        - text: {yaml_value(ui['letter'])}
          href: {lang}/{diatribe_path(letter['slug'])}.qmd
        - text: "---"
{chr(10).join(sections)}
        - text: "---"
        - text: {yaml_value(ui['credits'])}
          href: {lang}/credits.qmd''')

    quarto_yml = f'''# FILE GENERATO. NON MODIFICARE A MANO.
# Modificare tools/site_config.py ed eseguire run.bat.
project:
  type: website
  output-dir: docs
  post-render: tools/4_finalize_seo.py
  # Only the generated pages: without this Quarto would also publish the
  # translator's Markdown files under translation/ and the README.
  render:
    - "index.qmd"
{chr(10).join(f'    - "{lang}/**/*.qmd"' for lang in LANG_ORDER)}
  resources:
    - .nojekyll
    - assets

website:
  title: {yaml_value(SITE_BRAND)}
  site-url: {SITE_URL}
  search: false
  page-navigation: false
  navbar:
    left:
{chr(10).join(navbar)}
    right:
{flags}
  sidebar:
{chr(10).join(sidebars)}

format:
  html:
    theme: cosmo
    css: styles.css
    include-in-header: site-head.html
    include-after-body:
      - lang-config.html
      - lang-switch.html
    toc: false
    smooth-scroll: true
    anchor-sections: false
    link-external-newwindow: true
    canonical-url: true
'''
    write_if_changed(ROOT / '_quarto.yml', quarto_yml)


# ---------------------------------------------------------------------------
# Head snippets and runtime configuration
# ---------------------------------------------------------------------------

def write_site_head():
    data = {
        '@context': 'https://schema.org',
        '@type': 'WebSite',
        'name': SITE_BRAND,
        'url': SITE_URL,
        'inLanguage': [LANGS[lang]['html_lang'] for lang in LANG_ORDER],
    }
    parts = []
    if GOATCOUNTER.strip():
        parts.append(
            f'<script data-goatcounter="https://{GOATCOUNTER.strip()}.goatcounter.com/count" '
            'async src="//gc.zgo.at/count.js"></script>'
        )
    parts += [
        '<script type="application/ld+json">',
        json.dumps(data, ensure_ascii=False, indent=2),
        '</script>',
    ]
    if GOOGLE_SITE_VERIFICATION.strip():
        parts.append('<meta name="google-site-verification" '
                     f'content="{esc(GOOGLE_SITE_VERIFICATION.strip())}">')
    write_if_changed(ROOT / 'site-head.html', '\n'.join(parts) + '\n')


def write_seo_head(lang):
    seo = LANGS[lang]['seo']
    data = {
        '@context': 'https://schema.org',
        '@type': 'Book',
        'name': f'{LANGS[lang]["author"]}, {LANGS[lang]["title"]}',
        'alternateName': seo['home_title'],
        'author': {'@type': 'Person', 'name': 'Epictetus'},
        'inLanguage': LANGS[lang]['html_lang'],
        'description': seo['book_description'],
        'url': f'{SITE_URL}{lang}/',
    }
    if lang == 'it':
        data['translator'] = [
            {'@type': 'SoftwareApplication', 'name': 'GPT-5.6 Sol'},
            {'@type': 'SoftwareApplication', 'name': 'Claude Opus 5.0'},
        ]
    elif lang == 'en':
        data['translator'] = {'@type': 'Person', 'name': 'George Long'}
    body = json.dumps(data, ensure_ascii=False, indent=2)
    write_if_changed(
        ROOT / lang / 'seo-head.html',
        f'<script type="application/ld+json">\n{body}\n</script>\n',
    )


def write_lang_config(diatribes, translations):
    """Settings lang-switch.html needs at runtime.

    The navbar is shared by the whole site and is written in the default
    language, so every one of its labels is listed here for the other two.
    """
    nav = {}
    for lang in LANG_ORDER:
        labels = {'credits.html': LANGS[lang]['ui']['credits']}
        for diatribe in diatribes:
            title = title_for(lang, diatribe, translations)[0]
            labels[f'{diatribe_path(diatribe["slug"])}.html'] = menu_label(lang, diatribe, title)
        nav[lang] = labels

    config = {
        'langs': LANG_ORDER,
        'default': DEFAULT_LANG,
        'pages': pages_list(diatribes),
        'brand': {lang: LANGS[lang]['brand'] for lang in LANG_ORDER},
        'nav': nav,
        # The navbar dropdowns have no href of their own, so they are
        # relabelled by position: one per book, in the order Quarto writes them.
        'books': {
            lang: [LANGS[lang]['book_label'](book)
                   for book in sorted(books_of(diatribes)) if book]
            for lang in LANG_ORDER
        },
    }
    write_if_changed(
        ROOT / 'lang-config.html',
        '<!-- FILE GENERATO. Modificare tools/site_config.py. -->\n'
        f'<script>\nwindow.EPICTETUS = {json.dumps(config, ensure_ascii=False, indent=1)};\n</script>\n',
    )


# ---------------------------------------------------------------------------
# Shared page pieces
# ---------------------------------------------------------------------------

def page_header(lang, title=None, sidebar_id=None, pagetitle=None,
                description=None, include_in_header=None, extra=()):
    parts = ['---']
    if title is not None:
        parts.append(f'title: {yaml_value(title)}')
    parts.append(f'lang: {LANGS[lang]["html_lang"]}')
    if pagetitle:
        parts.append(f'pagetitle: {yaml_value(pagetitle)}')
        parts.append('title-prefix: ""')
    if description:
        parts.append(f'description-meta: {yaml_value(description)}')
    if sidebar_id:
        parts.append(f'sidebar: {sidebar_id}')
    else:
        parts.append('sidebar: false')
    parts += list(extra)
    if include_in_header:
        parts += ['format:', '  html:', f'    include-in-header: {include_in_header}']
    parts += ['---', '', GENERATED_FILE_NOTE, '']
    return parts


def cover_hero(lang, href):
    """The Italian cover, linked to the downloadable PDF."""
    cfg = LANGS[lang]
    label = f'{cfg["author"]} — {cfg["title"]}'
    return one_block(f'''<div class="cover-hero">
<a class="cover-download" href="{href}" aria-label="Scarica il libro in PDF">
<div class="cover-plate" role="img" aria-label="{esc(label)}">
<p class="cover-author">{esc(cfg['author'])}</p>
<h1 class="cover-title">{esc(cfg['title'])}</h1>
<p class="cover-subtitle">{esc(cfg['cover_subtitle'])}</p>
</div>
</a>
</div>''')


def pdf_download(href, label):
    """A compact, explicit PDF download control for the Italian home page."""
    return one_block(f'''<div class="site-download">
<a href="{href}" aria-label="{esc(label)}">
<svg class="pdf-icon" viewBox="0 0 24 28" aria-hidden="true" focusable="false">
<path d="M4.5 1.5h10l5 5v20h-15z"/><path d="M14.5 1.5v5h5"/>
<text x="12" y="20.2" text-anchor="middle">PDF</text>
</svg>
<span>{esc(label)}</span>
</a>
</div>''')


def book_grids(lang, diatribes, translations, prefix=''):
    """One card per diatribe, grouped by book.

    Arrian's dedicatory letter is left out: it is a page of front matter, not a
    diatribe, and a book of one card at the top of the home page only delays the
    text.  It stays one click away, in the navbar and in the sidebar.
    """
    ui = LANGS[lang]['ui']
    out = []
    for book, items in books_of(diatribes).items():
        if book == 0:
            continue
        out += [
            f'<h2 id="book-{book}">{esc(LANGS[lang]["book_label"](book))}</h2>',
            '',
            '<div class="chapter-grid">',
        ]
        for diatribe in items:
            title, fallback = title_for(lang, diatribe, translations)
            count = len(diatribe['sections'])
            word = ui['section'] if count == 1 else ui['sections']
            number = f'{ui["diatribe"]} {diatribe_number(lang, diatribe["chapter"])}'
            title_attr = ' lang="en"' if fallback else ''
            out.append(
                f'<a class="chapter-card" href="{prefix}{diatribe_path(diatribe["slug"])}.html">'
                f'<span class="chapter-number">{esc(number)}</span>'
                f'<span class="chapter-title"{title_attr}>{esc(title)}</span>'
                f'<span class="chapter-count">{count} {esc(word)}</span></a>'
            )
        out += ['</div>', '']
    return out


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

def write_root_index(diatribes, translations, intro):
    """Language-choice landing page, indexable and complete on its own."""
    lang = DEFAULT_LANG
    choices = '\n'.join(
        f'<a class="lang-choice" href="{other}/index.html">'
        f'<span class="ep-lang" data-lang="{other}">{esc(LANGS[other]["label"])}</span>'
        f'<span class="lang-choice-note">{esc(LANGS[other]["title"])}</span></a>'
        for other in LANG_ORDER
    )
    parts = page_header(
        lang,
        pagetitle=ROOT_HOME_TITLE,
        description=ROOT_HOME_DESCRIPTION,
    )
    parts += [
        cover_hero(lang, PDF_FILENAME), '',
        '<div class="lang-chooser">', choices, '</div>', '',
        prose(intro, lang, 'site-note'), '',
    ]
    parts += book_grids(lang, diatribes, translations, prefix=f'{lang}/')
    write_if_changed(ROOT / 'index.qmd', '\n'.join(parts))


def write_index(lang, diatribes, translations, intro, pdf_ready):
    cfg = LANGS[lang]
    ui = cfg['ui']
    parts = page_header(
        lang,
        sidebar_id=lang,
        pagetitle=cfg['seo']['home_title'],
        description=cfg['seo']['home_description'],
        include_in_header='seo-head.html',
    )
    if lang == PDF_LANG and pdf_ready:
        parts += [cover_hero(lang, f'../{PDF_FILENAME}'), '']
    parts += [prose(intro, lang, 'site-note'), '']
    parts += [f'<div class="site-usage">{esc(ui["usage"])}</div>', '']
    if lang == PDF_LANG and pdf_ready:
        parts += [pdf_download(f'../{PDF_FILENAME}', ui['download']), '']
    parts += book_grids(lang, diatribes, translations)
    write_if_changed(ROOT / lang / 'index.qmd', '\n'.join(parts))


def write_credits(lang, credits):
    cfg = LANGS[lang]
    parts = page_header(
        lang,
        title=cfg['ui']['credits'],
        sidebar_id=lang,
        pagetitle=cfg['seo']['credits_title'],
        description=cfg['seo']['credits_description'],
    )
    parts += [prose(credits, lang, 'site-note credits-note'), '']
    write_if_changed(ROOT / lang / 'credits.qmd', '\n'.join(parts))


def italian_html(text):
    """One section of the translator's Markdown, as HTML.

    A section is usually a single paragraph and is left as running text; where
    the translator has broken it in two, both halves become paragraphs.
    """
    paragraphs = [
        inline_markup(' '.join(line.strip() for line in block.splitlines()))
        for block in re.split(r'\n\s*\n', text.strip()) if block.strip()
    ]
    if len(paragraphs) == 1:
        return paragraphs[0]
    return ''.join(f'<p>{paragraph}</p>' for paragraph in paragraphs)


def greek_section_html(fragment):
    """Make a TEI paragraph fragment safe inside one numbered section.

    A paragraph in the source can cross a section boundary, leaving an opening
    or closing ``p`` tag in only one fragment. The section's own ``div`` already
    supplies the block container, so retain internal breaks but discard those
    unmatched paragraph wrappers.
    """
    body = re.sub(r'</p>\s*<p(?:\s[^>]*)?>', '<br><br>', fragment)
    return re.sub(r'</?p(?:\s[^>]*)?>', '', body)


def section_articles(lang, diatribe, italian):
    """The numbered sections of a diatribe, as the Greek or Italian edition shows them."""
    out = ['<div class="section-list">']
    for section in diatribe['sections']:
        number = section['n']
        anchor = f's-{number}'
        if lang == 'grc':
            body, fallback = greek_section_html(section['html']), False
        else:
            text = italian.get(number, '')
            body, fallback = ((italian_html(text), False) if text else
                              (greek_section_html(section['html']), True))
        classes = 'section-text' + (' section-fallback' if fallback else '')
        lang_attr = ' lang="grc"' if (fallback or lang == 'grc') else ''
        out.append(
            f'<article class="section" id="{anchor}">'
            f'<a class="ref" href="#{anchor}">{number}</a>'
            f'<div class="{classes}"{lang_attr}>{body}</div>'
            '</article>'
        )
    out.append('</div>')
    return one_block('\n'.join(out))


def english_body(diatribe, muted=False):
    """Long's paragraphs, as he wrote them."""
    classes = 'paragraph-list' + (' section-fallback' if muted else '')
    attr = ' lang="en"' if muted else ''
    return one_block(
        f'<div class="{classes}"{attr}>\n' + '\n'.join(diatribe['en_paragraphs']) + '\n</div>'
    )


def english_notes(lang, diatribe):
    if not diatribe['en_notes']:
        return []
    items = '\n'.join(
        f'<li class="note" id="note-{note["n"]}" role="doc-endnote">{note["html"]}'
        f'<a class="note-back" href="#noteref-{note["n"]}" aria-label="back to the text">&#8617;</a></li>'
        for note in diatribe['en_notes']
    )
    return [one_block(
        f'<section class="notes">\n<h2>{esc(LANGS[lang]["ui"]["notes"])}</h2>\n'
        f'<ol class="note-list">\n{items}\n</ol>\n</section>'
    ), '']


def write_diatribes(lang, diatribes, translations):
    directory = ROOT / lang / DIATRIBE_DIR
    directory.mkdir(parents=True, exist_ok=True)

    cfg = LANGS[lang]
    ui = cfg['ui']
    for position, diatribe in enumerate(diatribes):
        title, fallback_title = title_for(lang, diatribe, translations)
        label = page_label(lang, diatribe)
        italian = translated_sections(diatribe, translations)
        done = sum(1 for section in diatribe['sections'] if italian.get(section['n']))

        seo = cfg['seo']
        keys = {'label': label, 'title': title}
        parts = page_header(
            lang,
            title=f'{label} — {title}',
            sidebar_id=lang,
            pagetitle=seo['diatribe_title'].format(**keys),
            description=seo['diatribe_description'].format(**keys),
        )

        # Meta line: which book this is, how long it is, how it is numbered.
        count = len(diatribe['sections'])
        word = ui['section'] if count == 1 else ui['sections']
        meta = [esc(cfg['book_label'](diatribe['book']))] if diatribe['book'] else []
        if lang == 'en':
            # Long's translation has no section numbers, only his paragraphs.
            paragraphs = len(diatribe['en_paragraphs'])
            unit = ui['paragraph'] if paragraphs == 1 else ui['paragraphs']
            meta.append(f'{paragraphs} {esc(unit)}')
        else:
            meta.append(f'{count} {esc(word)}')
        if diatribe['book']:
            meta.append(f'<span class="canonical" title="{esc(ui["reference"])}">'
                        f'{ROMAN[diatribe["book"]]} {diatribe["chapter"]}</span>')
        parts += [f'<div class="diatribe-meta">{" · ".join(meta)}</div>', '']

        if lang == 'en' and diatribe['en_title_markers']:
            markers = ''.join(diatribe['en_title_markers'])
            parts += [f'<div class="title-note">{esc(ui["title_note"])}{markers}</div>', '']

        if lang == 'it' and fallback_title and done:
            parts += [f'<div class="lang-pending">{esc(IT_PENDING_TITLE)}</div>', '']

        previous = diatribes[position - 1] if position else None
        following = diatribes[position + 1] if position + 1 < len(diatribes) else None
        parts += [navigation(lang, previous, following), '']

        if lang == 'it' and done == 0:
            parts += [f'<div class="lang-pending">{esc(IT_PENDING_ALL)}</div>', '']
            parts += [english_body(diatribe, muted=True), '']
            parts += english_notes(lang, diatribe)
        elif lang == 'en':
            parts += [english_body(diatribe), '']
            parts += english_notes(lang, diatribe)
        else:
            if lang == 'it' and done < count:
                parts += [f'<div class="lang-pending">{esc(IT_PENDING_SOME)}</div>', '']
            parts += [section_articles(lang, diatribe, italian), '']

        parts += [navigation(lang, previous, following, bottom=True), '']
        write_if_changed(directory / f'{diatribe["slug"]}.qmd', '\n'.join(parts))

    # Drop any page left over from a diatribe that no longer exists.
    current = {f'{diatribe["slug"]}.qmd' for diatribe in diatribes}
    for old in directory.glob('*.qmd'):
        if old.name not in current:
            old.unlink()


def navigation(lang, previous, following, bottom=False):
    ui = LANGS[lang]['ui']
    left = (f'<a href="{previous["slug"]}.html">{esc(ui["previous"])}</a>'
            if previous else '<span></span>')
    right = (f'<a href="{following["slug"]}.html">{esc(ui["next"])}</a>'
             if following else '<span></span>')
    home = f'<a class="chapter-home" href="../index.html">{esc(ui["home"])}</a>'
    css = 'chapter-nav chapter-nav-bottom' if bottom else 'chapter-nav'
    return f'<nav class="{css}">{left}{home}{right}</nav>'


# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------

def copy_assets():
    (ASSETS / 'flags').mkdir(parents=True, exist_ok=True)
    for lang in LANG_ORDER:
        name = LANGS[lang]['flag']
        source = DATA / 'flags' / name
        if not source.exists():
            raise SystemExit(f'Missing flag image: {source}')
        copy_if_changed(source, ASSETS / 'flags' / name)
    # The site uses the compressed cover (113 KB against 2.1 MB); the full-size
    # PNG is for the PDF only.  If data/cover.png is ever replaced, remake it:
    #   python -c "from PIL import Image; im=Image.open('data/cover.png');
    #   im.resize((800, round(im.height*800/im.width))).convert('RGB').save(
    #   'data/cover-web.jpg', quality=84, optimize=True, progressive=True)"
    cover = DATA / 'cover-web.jpg'
    if not cover.exists():
        raise SystemExit(f'Missing cover image: {cover}')
    copy_if_changed(cover, ASSETS / 'cover.jpg')


# ---------------------------------------------------------------------------

def report(diatribes, translations):
    done, total, complete = translation_store.progress(diatribes, translations)
    percent = 100 * done / total if total else 0
    print(f'  italiano: {done}/{total} sezioni tradotte ({percent:.1f}%), '
          f'{len(complete)}/{len(diatribes)} diatribe complete.')
    if complete:
        print(f'      complete: {", ".join(complete[:12])}'
              f'{" …" if len(complete) > 12 else ""}')
    elif done:
        print('      nessuna diatriba ancora completa: dove manca una sezione '
              'la pagina italiana mostra il greco.')
    else:
        print('      nessuna diatriba ancora tradotta: '
              'le pagine italiane mostrano la traduzione inglese.')


def main():
    data = load_json('discourses.json')
    diatribes = data['diatribes']
    intro = load_json('intro.json')
    credits = load_json('credits.json')
    translations = translation_store.load_all(diatribes)
    # The same rule tools/3_generate_pdf_book.py uses to decide whether there is
    # a book to print: Arrian's letter alone does not make one.
    pdf_ready = any(
        translated_sections(diatribe, translations)
        for diatribe in diatribes if diatribe['book']
    )

    copy_assets()
    write_quarto_yml(diatribes, translations)
    write_lang_config(diatribes, translations)
    write_site_head()
    write_root_index(diatribes, translations, intro)

    for lang in LANG_ORDER:
        (ROOT / lang).mkdir(exist_ok=True)
        write_seo_head(lang)
        write_index(lang, diatribes, translations, intro, pdf_ready=pdf_ready)
        write_credits(lang, credits)
        write_diatribes(lang, diatribes, translations)

    pages = len(pages_list(diatribes))
    print(f'Generate {pages} pagine per lingua ({", ".join(LANG_ORDER)}), '
          f'{pages * len(LANG_ORDER) + 1} in tutto.')
    report(diatribes, translations)


if __name__ == '__main__':
    main()
