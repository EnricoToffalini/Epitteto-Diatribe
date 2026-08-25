"""Read the Italian source files used by the site and PDF generators.

One file per diatribe, in `translation/it/`, named after the diatribe:

    translation/it/1-01.md     ->  Book I, discourse 1

The format is plain Markdown, so the completed edition remains easy to correct,
review and diff:

    ---
    ref: 1.1
    titolo: Su ciò che dipende da noi e ciò che non dipende da noi
    titolo_grc: περὶ τῶν ἐφʼ ἡμῖν καὶ οὐκ ἐφʼ ἡμῖν
    titolo_en: Of the things which are in our power, and not in our power
    ---

    ## 1.1.1

    > τῶν ἄλλων δυνάμεων οὐδεμίαν εὑρήσετε αὐτὴν αὑτῆς θεωρητικήν…

    Delle altre facoltà non ne troverete nessuna capace di osservare sé stessa…

The parser follows three rules:

  * `## <libro>.<diatriba>.<sezione>` opens a section;
  * lines beginning with `>` are the Greek original, kept only for reference and
    ignored by the site;
  * everything else is the Italian text. `TODO` or blank text is rejected by
    the validation step in the final build.
"""

from pathlib import Path
import re

from site_config import ROOT

TRANSLATION_DIR = ROOT / 'translation' / 'it'
TODO = 'TODO'

SECTION_RE = re.compile(r'^##\s+(\d+)\.(\d+)\.(\d+)\s*$')


def path_for(slug):
    return TRANSLATION_DIR / f'{slug}.md'


def _split_front_matter(text):
    if not text.startswith('---'):
        return {}, text
    end = text.find('\n---', 3)
    if end == -1:
        return {}, text
    block = text[3:end]
    rest = text[end + 4:].lstrip('\n')
    fields = {}
    for line in block.splitlines():
        line = line.strip()
        if not line or line.startswith('#') or ':' not in line:
            continue
        key, value = line.split(':', 1)
        fields[key.strip()] = value.strip()
    return fields, rest


def parse(text):
    """Return (fields, {section number: italian text}) for one file."""
    fields, body = _split_front_matter(text)
    sections = {}
    current = None
    buffer = []

    def flush():
        if current is None:
            return
        value = '\n'.join(buffer).strip()
        value = re.sub(r'\n{3,}', '\n\n', value)
        sections[current] = '' if value == TODO else value

    for line in body.splitlines():
        match = SECTION_RE.match(line.strip())
        if match:
            flush()
            current, buffer = int(match.group(3)), []
            continue
        if current is None:
            continue
        stripped = line.strip()
        if stripped.startswith('>') or stripped.startswith('<!--') or stripped.startswith('-->'):
            continue
        buffer.append(line.rstrip())
    flush()
    return fields, sections


def load(slug):
    path = path_for(slug)
    if not path.exists():
        return {}, {}
    return parse(path.read_text(encoding='utf-8'))


def load_all(diatribes):
    """Italian text and titles for every diatribe, keyed by slug."""
    out = {}
    for diatribe in diatribes:
        fields, sections = load(diatribe['slug'])
        title = fields.get('titolo', '').strip()
        out[diatribe['slug']] = {
            'title': '' if title == TODO else title,
            'sections': {n: text for n, text in sections.items() if text},
        }
    return out


def progress(diatribes, translations):
    """(done, total) sections, and the list of fully translated diatribes."""
    done = total = 0
    complete = []
    for diatribe in diatribes:
        known = [section['n'] for section in diatribe['sections']]
        have = translations.get(diatribe['slug'], {}).get('sections', {})
        got = sum(1 for n in known if have.get(n))
        done += got
        total += len(known)
        if known and got == len(known):
            complete.append(diatribe['ref'])
    return done, total, complete
