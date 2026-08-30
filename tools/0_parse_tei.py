"""Turn the two Perseus TEI files into one structured JSON file.

Input (sources/):
    tlg0557.tlg001.perseus-grc2.xml   Schenkl's Greek edition (Teubner, 1916)
    tlg0557.tlg001.perseus-eng3.xml   George Long's English translation (1890)

Output:
    data/discourses.json

The two editions share the same skeleton -- four books plus Arrian's opening
letter, and inside each book a numbered series of diatribes -- but they do not
share the same unit below that level:

  * the Greek edition carries the canonical section numbers (I 1, 7 and so on),
    so it is stored as a list of numbered sections;
  * Long's translation has no section numbers at all, only his own long
    paragraphs, so it is stored as a list of paragraphs plus his footnotes.

Both are therefore kept as they are, and the Italian translation follows the
Greek sections, which is the numbering every edition and commentary cites.
Inline TEI markup is converted to a small, fixed set of HTML tags here, once,
so that the site generator and the PDF generator never have to look at XML.
"""

import sys
from pathlib import Path
import html
import json
import re
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))

from io_utils import write_if_changed

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / 'sources'
GRC_XML = SOURCES / 'tlg0557.tlg001.perseus-grc2.xml'
ENG_XML = SOURCES / 'tlg0557.tlg001.perseus-eng3.xml'
OUT_JSON = ROOT / 'data' / 'discourses.json'

TEI = 'http://www.tei-c.org/ns/1.0'
NS = '{%s}' % TEI
XML_LANG = '{http://www.w3.org/XML/1998/namespace}lang'

# Books, in the order they are published.  Book 0 holds the single "chapter"
# that is Arrian's dedicatory letter to Lucius Gellius.
BOOK_NUMBERS = [0, 1, 2, 3, 4]


def tag_of(element):
    return element.tag.replace(NS, '') if isinstance(element.tag, str) else ''


def esc(text):
    return html.escape(text or '', quote=False)


def squeeze(text):
    """Collapse the whitespace TEI files use for indentation."""
    return re.sub(r'\s+', ' ', text or '')


class Converter:
    """Convert TEI content into the site's small HTML vocabulary.

    Footnotes are collected rather than inlined: Long's notes are long and
    often longer than the paragraph carrying them, so each page prints them
    once at the end and links to them from a marker in the text.
    """

    # Elements whose content is kept but which carry no meaning worth marking.
    TRANSPARENT = {'placeName', 'date', 'name', 'persName', 'num', 'seg',
                   'hi', 'corr', 'reg', 'said', 'milestone', 'lb'}
    # Elements dropped along with their content.
    DROPPED = {'pb', 'gap', 'orig', 'abbr'}

    def __init__(self, collect_notes=True):
        self.collect_notes = collect_notes
        self.notes = []

    # -- helpers ----------------------------------------------------------

    def children(self, element):
        return ''.join(self.node(child) for child in element)

    def content(self, element):
        return esc(squeeze(element.text)) + self.children(element)

    def wrap(self, element, before, after=''):
        return before + self.content(element) + after

    # -- one node ---------------------------------------------------------

    def node(self, element):
        tag = tag_of(element)
        tail = esc(squeeze(element.tail))

        if tag in self.DROPPED:
            if tag == 'gap':
                return '<span class="ed-gap" title="lacuna">&hellip;</span>' + tail
            return tail

        if tag == 'note':
            return self.note(element) + tail

        if tag in self.TRANSPARENT:
            return self.content(element) + tail

        if tag == 'p':
            return '<p>' + self.content(element) + '</p>' + tail

        if tag == 'q':
            return self.wrap(element, '<q>', '</q>') + tail

        if tag == 'quote':
            lang = element.get(XML_LANG)
            attr = f' lang="{lang}" class="foreign"' if lang and lang != 'eng' else ''
            if element.find(NS + 'l') is not None or element.find(NS + 'lg') is not None:
                # A span, not a blockquote: verse quotations sit inside a
                # paragraph, where a block element would break the markup.
                return self.wrap(
                    element, f'<span class="verse-quote"{attr}>', '</span>'
                ) + tail
            return self.wrap(element, f'<q{attr}>', '</q>') + tail

        if tag == 'cit':
            return self.wrap(element, '<span class="cit">', '</span>') + tail

        if tag == 'bibl' or tag == 'title':
            return self.wrap(element, '<cite>', '</cite>') + tail

        if tag == 'lg':
            return self.wrap(element, '<span class="lg">', '</span>') + tail

        if tag == 'l':
            # No <br>: styles.css sets each line as a block of its own.
            return self.wrap(element, '<span class="l">', '</span>') + tail

        if tag == 'foreign':
            lang = element.get(XML_LANG) or 'grc'
            return self.wrap(element, f'<span class="foreign" lang="{lang}">', '</span>') + tail

        if tag in ('emph', 'gloss', 'label', 'soCalled'):
            return self.wrap(element, '<em>', '</em>') + tail

        # Schenkl's editorial marks: deletions in square brackets, additions in
        # angle brackets, exactly as the printed Teubner text shows them.
        if tag == 'del':
            return self.wrap(element, '<span class="ed-del">[', ']</span>') + tail

        if tag == 'add':
            return self.wrap(element, '<span class="ed-add">&lang;', '&rang;</span>') + tail

        if tag == 'sic':
            return self.wrap(element, '<span class="ed-sic">', '</span>') + tail

        if tag == 'choice':
            corr = element.find(NS + 'corr')
            chosen = corr if corr is not None else element.find(NS + 'sic')
            return (self.content(chosen) if chosen is not None else '') + tail

        # Anything unforeseen keeps its text rather than losing it.
        return self.content(element) + tail

    def note(self, element):
        if not self.collect_notes:
            return ''
        body = self.blocks(element)
        self.notes.append({'n': len(self.notes) + 1, 'html': body})
        n = len(self.notes)
        return (
            f'<a class="note-ref" id="noteref-{n}" href="#note-{n}" '
            f'role="doc-noteref" aria-label="note {n}"><sup>{n}</sup></a>'
        )

    def blocks(self, element):
        """Render an element whose children are paragraphs (a note, a section)."""
        out = []
        loose = esc(squeeze(element.text))
        for child in element:
            if tag_of(child) == 'p':
                if loose.strip():
                    out.append(f'<p>{loose.strip()}</p>')
                    loose = ''
                out.append(self.node(child))
            else:
                loose += self.node(child)
        if loose.strip():
            out.append(f'<p>{loose.strip()}</p>')
        return '\n'.join(out)


def clean_html(text):
    text = re.sub(r'\s+</p>', '</p>', text)
    text = re.sub(r'<p>\s+', '<p>', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()


def plain_text(fragment):
    text = re.sub(r'<[^>]+>', '', fragment)
    return html.unescape(re.sub(r'\s+', ' ', text)).strip()


def top_division(path):
    root = ET.parse(path).getroot()
    body = root.find('.//' + NS + 'body')
    return body.find(NS + 'div')


def text_without_notes(element):
    """All the text of an element, minus any footnote hanging inside it."""
    parts = [element.text or '']
    for child in element:
        if tag_of(child) != 'note':
            parts.append(text_without_notes(child))
        parts.append(child.tail or '')
    return ''.join(parts)


def head_text(division):
    head = division.find(NS + 'head')
    if head is None:
        return ''
    return squeeze(text_without_notes(head)).strip().rstrip('.').strip()


def read_greek():
    """Greek: book -> chapter -> numbered section, one paragraph each."""
    out = {}
    top = top_division(GRC_XML)
    for book in top.findall(NS + 'div'):
        for chapter in book.findall(NS + 'div'):
            sections = []
            for section in chapter.findall(NS + 'div'):
                number = section.get('n')
                if not number or not number.isdigit():
                    continue
                converter = Converter(collect_notes=False)
                fragment = clean_html(converter.blocks(section))
                # Sections are single paragraphs; the wrapper only gets in the
                # way when the site puts each one in its own <article>.
                inner = re.fullmatch(r'<p>(.*)</p>', fragment, flags=re.S)
                if inner:
                    fragment = inner.group(1)
                sections.append({
                    'n': int(number),
                    'html': fragment,
                    'text': plain_text(fragment),
                })
            out[(book.get('n'), chapter.get('n'))] = {
                'title': head_text(chapter),
                'sections': sections,
            }
    return out


MARKER = re.compile(r'<a class="note-ref".*?</a>', flags=re.S)


def read_english():
    """English: book -> chapter -> paragraphs, with Long's footnotes.

    A handful of Long's notes comment on the chapter title rather than on any
    sentence in it.  In the TEI they sit inside <head> or immediately after it;
    here their markers are kept apart, so that the page can show them under the
    title instead of stranding a lone superscript in a paragraph of its own.
    """
    out = {}
    top = top_division(ENG_XML)
    for book in top.findall(NS + 'div'):
        for chapter in book.findall(NS + 'div'):
            converter = Converter(collect_notes=True)
            head = chapter.find(NS + 'head')
            title_markers = MARKER.findall(converter.content(head)) if head is not None else []
            paragraphs = []
            for child in chapter:
                tag = tag_of(child)
                if tag == 'head':
                    continue
                fragment = clean_html(converter.node(child))
                if tag == 'note':
                    # A note anchored to the chapter as a whole: keep its marker
                    # with the title, or with the paragraph it followed.
                    if paragraphs:
                        paragraphs[-1] = re.sub(
                            r'</p>\s*$', fragment + '</p>', paragraphs[-1]
                        )
                    else:
                        title_markers += MARKER.findall(fragment)
                    continue
                if plain_text(fragment):
                    if not fragment.startswith('<'):
                        fragment = f'<p>{fragment}</p>'
                    paragraphs.append(fragment)
            out[(book.get('n'), chapter.get('n'))] = {
                'title': head_text(chapter),
                'title_markers': title_markers,
                'paragraphs': paragraphs,
                'notes': [
                    {'n': note['n'], 'html': clean_html(note['html'])}
                    for note in converter.notes
                ],
            }
    return out


def main():
    greek = read_greek()
    english = read_english()

    missing = set(greek) ^ set(english)
    if missing:
        raise SystemExit(f'The two editions do not cover the same chapters: {sorted(missing)}')

    diatribes = []
    for book_key, chapter_key in sorted(greek, key=lambda k: (int(k[0]), int(k[1]))):
        book, chapter = int(book_key), int(chapter_key)
        grc = greek[(book_key, chapter_key)]
        eng = english[(book_key, chapter_key)]
        diatribes.append({
            'book': book,
            'chapter': chapter,
            'ref': f'{book}.{chapter}',
            'slug': f'{book}-{chapter:02d}',
            'title': {'grc': grc['title'], 'en': eng['title']},
            'sections': grc['sections'],
            'en_paragraphs': eng['paragraphs'],
            'en_title_markers': eng['title_markers'],
            'en_notes': eng['notes'],
        })

    data = {
        'source': {
            'greek': {
                'urn': 'urn:cts:greekLit:tlg0557.tlg001.perseus-grc2',
                'edition': 'Epicteti dissertationes ab Arriano digestae',
                'editor': 'Heinrich Schenkl',
                'imprint': 'Leipzig: Teubner, 1916',
            },
            'english': {
                'urn': 'urn:cts:greekLit:tlg0557.tlg001.perseus-eng3',
                'edition': 'The Discourses of Epictetus, with the Encheiridion and Fragments',
                'translator': 'George Long',
                'imprint': 'London: George Bell and Sons, 1890',
            },
            'provider': 'Perseus Digital Library, Tufts University',
            'licence': 'CC BY-SA 4.0',
            'licence_url': 'https://creativecommons.org/licenses/by-sa/4.0/',
        },
        'books': BOOK_NUMBERS,
        'diatribes': diatribes,
    }
    write_if_changed(OUT_JSON, json.dumps(data, ensure_ascii=False, indent=1))

    sections = sum(len(d['sections']) for d in diatribes)
    paragraphs = sum(len(d['en_paragraphs']) for d in diatribes)
    notes = sum(len(d['en_notes']) for d in diatribes)
    print(f'Parsed {len(diatribes)} diatribes in {len(BOOK_NUMBERS)} books: '
          f'{sections} Greek sections, {paragraphs} English paragraphs, {notes} notes.')


if __name__ == '__main__':
    main()
