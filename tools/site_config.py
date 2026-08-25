"""Everything that is decided once and used by every tool in this project.

Editing this file is how the site changes: wording, languages, URLs, and the
few numbers that describe the book itself.  The tools never hard-code any of it.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SITE_URL = 'https://enricotoffalini.github.io/Epitteto-Diatribe/'
SITE_BRAND = 'Epitteto · Diatribe'

# GoatCounter code as used on the Bhagavad Gita site ("gita" there).  Left empty
# until the site is registered, so no build ever pings a non-existent endpoint.
GOATCOUNTER = ''

# Google Search Console token only (not the whole <meta> element).  While it is
# empty no verification tag is written, so a placeholder can never be published.
GOOGLE_SITE_VERIFICATION = ''

DEFAULT_LANG = 'it'          # the main edition: the site root points here
LANG_ORDER = ['it', 'en', 'grc']

PDF_LANG = 'it'              # the downloadable book exists for Italian only
PDF_FILENAME = 'epitteto-diatribe-it.pdf'

# Directory shared by the three editions.  The language switcher relies on every
# page having a counterpart at the same relative path in the other languages.
DIATRIBE_DIR = 'diatribe'

ROMAN = {0: '', 1: 'I', 2: 'II', 3: 'III', 4: 'IV'}

# 6 is the stigma and 90 the koppa, as in polytonic numbering.
_GREEK_UNITS = ' αβγδεϛζηθ'
_GREEK_TENS = ' ικλμνξοπϟ'


def greek_numeral(value, upper=False):
    """Small Greek numeral with keraia: 1 -> αʹ, 13 -> ιγʹ, 30 -> λʹ.

    Books are numbered with capitals (Αʹ, Βʹ) and discourses with small letters,
    as printed editions of the Discourses do.
    """
    if not 1 <= value <= 99:
        return str(value)
    tens, units = divmod(value, 10)
    letters = (_GREEK_TENS[tens] if tens else '') + (_GREEK_UNITS[units] if units else '')
    letters = letters.strip()
    return (letters.upper() if upper else letters) + 'ʹ'


LANGS = {
    'it': {
        'label': 'Italiano',
        'html_lang': 'it',
        'flag': 'it.png',
        'title': 'Diatribe',
        'author': 'Epitteto',
        'cover_subtitle': 'raccolte da Arriano',
        'brand': 'Epitteto · Diatribe',
        'book_label': lambda n: f'Libro {ROMAN[n]}',
        'diatribe_label': lambda n: f'Diatriba {n}',
        'ui': {
            'home': 'Home',
            'books': 'Libri',
            'letter': 'Lettera di Arriano',
            'diatribe': 'Diatriba',
            'diatribe_at': 'Diatriba',
            'section': 'sezione',
            'sections': 'sezioni',
            'previous': 'Diatriba precedente',
            'next': 'Diatriba successiva',
            'credits': 'Fonti e crediti',
            'notes': 'Note',
            'title_note': 'Nota sul titolo',
            'download': 'Scarica il libro in PDF (italiano)',
            'usage': 'Le tre edizioni — italiana, inglese e greca — hanno le stesse pagine: '
                     'le bandiere in alto passano da una all’altra restando sulla stessa diatriba.',
            'reference': 'Riferimento canonico',
        },
        'seo': {
            'home_title': 'Epitteto, Diatribe — traduzione italiana',
            'home_description': (
                'Le Diatribe di Epitteto raccolte da Arriano, in traduzione italiana, '
                'con il testo greco originale e la traduzione inglese di George Long.'
            ),
            'credits_title': 'Fonti e crediti — Diatribe di Epitteto',
            'credits_description': (
                'Edizioni, traduttori e licenze dei testi usati in questo sito: '
                'Schenkl per il greco, George Long per l’inglese, Perseus Digital Library.'
            ),
            'diatribe_title': '{label} — {title} — Epitteto, Diatribe',
            'diatribe_description': (
                '{label}: «{title}». Le Diatribe di Epitteto raccolte da Arriano, '
                'in traduzione italiana.'
            ),
            'book_description': (
                'Le Diatribe di Epitteto raccolte da Arriano, in traduzione italiana.'
            ),
        },
    },
    'en': {
        'label': 'English',
        'html_lang': 'en',
        'flag': 'en.png',
        'title': 'Discourses',
        'author': 'Epictetus',
        'cover_subtitle': 'recorded by Arrian',
        'brand': 'Epictetus · Discourses',
        'book_label': lambda n: f'Book {ROMAN[n]}',
        'diatribe_label': lambda n: f'Discourse {n}',
        'ui': {
            'home': 'Home',
            'books': 'Books',
            'letter': 'Arrian’s letter',
            'diatribe': 'Discourse',
            'diatribe_at': 'Discourse',
            'section': 'section',
            'sections': 'sections',
            # Long's translation is measured in his paragraphs, not in sections.
            'paragraph': 'paragraph',
            'paragraphs': 'paragraphs',
            'previous': 'Previous discourse',
            'next': 'Next discourse',
            'credits': 'Sources and credits',
            'notes': 'Notes',
            'title_note': 'Note on the title',
            'download': '',
            'usage': 'The three editions — Italian, English and Greek — have the same pages: '
                     'the flags at the top move between them without leaving the discourse.',
            'reference': 'Canonical reference',
        },
        'seo': {
            'home_title': 'Epictetus, Discourses — English translation by George Long',
            'home_description': (
                'The Discourses of Epictetus as recorded by Arrian, in George Long’s '
                'English translation, beside the Greek text and an Italian translation.'
            ),
            'credits_title': 'Sources and credits — Epictetus, Discourses',
            'credits_description': (
                'Editions, translators and licences of the texts used on this site: '
                'Schenkl for the Greek, George Long for the English, Perseus Digital Library.'
            ),
            'diatribe_title': '{label} — {title} — Epictetus, Discourses',
            'diatribe_description': (
                '{label}: “{title}”. The Discourses of Epictetus, in George Long’s '
                'English translation, with his notes.'
            ),
            'book_description': (
                'The Discourses of Epictetus, recorded by Arrian, in George Long’s '
                'English translation.'
            ),
        },
    },
    'grc': {
        'label': 'Ἑλληνιστί',
        'html_lang': 'grc',
        'flag': 'grc.png',
        'title': 'Διατριβαί',
        'author': 'Ἐπίκτητος',
        'cover_subtitle': 'ὑπὸ Ἀρριανοῦ ἀναγεγραμμέναι',
        'brand': 'Ἐπίκτητος · Διατριβαί',
        'book_label': lambda n: f'Βιβλίον {greek_numeral(n, upper=True)}' if n else 'Ἐπιστολή',
        'diatribe_label': lambda n: f'Διατριβὴ {greek_numeral(n)}',
        'ui': {
            'home': 'Ἀρχή',
            'books': 'Βιβλία',
            'letter': 'Ἀρριανοῦ ἐπιστολή',
            'diatribe': 'Διατριβή',
            'diatribe_at': 'Διατριβὴ',   # before a numeral the accent turns grave
            'section': 'τμῆμα',
            'sections': 'τμήματα',
            'previous': 'ἡ προτέρα διατριβή',
            'next': 'ἡ ἑπομένη διατριβή',
            'credits': 'Περὶ τῆς ἐκδόσεως',
            'notes': 'Σημειώσεις',
            'title_note': 'Σημείωσις περὶ τοῦ τίτλου',
            'download': '',
            'usage': 'Αἱ τρεῖς ἐκδόσεις — ἡ Ἰταλική, ἡ Ἀγγλική, ἡ Ἑλληνική — τὰς αὐτὰς σελίδας ἔχουσιν· '
                     'τὰ σημεῖα τὰ ἄνω μεταφέρει ἀπὸ τῆς ἑτέρας εἰς τὴν ἑτέραν ἐν τῇ αὐτῇ διατριβῇ.',
            'reference': 'Παραπομπή',
        },
        'seo': {
            'home_title': 'Ἐπικτήτου Διατριβαί — τὸ ἑλληνικὸν κείμενον (Schenkl, 1916)',
            'home_description': (
                'Ἀρριανοῦ τῶν Ἐπικτήτου Διατριβῶν βιβλία τέσσαρα, κατὰ τὴν ἔκδοσιν '
                'Ἑινρίκου Schenkl (Teubner, 1916).'
            ),
            'credits_title': 'Περὶ τῆς ἐκδόσεως — Ἐπικτήτου Διατριβαί',
            'credits_description': (
                'Αἱ ἐκδόσεις καὶ αἱ ἄδειαι τῶν κειμένων τοῦδε τοῦ τόπου: Schenkl, George Long, '
                'Perseus Digital Library.'
            ),
            'diatribe_title': '{label} — {title} — Ἐπικτήτου Διατριβαί',
            'diatribe_description': (
                '{label}· «{title}». Ἀρριανοῦ τῶν Ἐπικτήτου Διατριβῶν, '
                'τὸ ἑλληνικὸν κείμενον.'
            ),
            'book_description': (
                'Ἀρριανοῦ τῶν Ἐπικτήτου Διατριβῶν βιβλία τέσσαρα, τὸ ἑλληνικὸν κείμενον.'
            ),
        },
    },
}

# Defensive notices: the validation step normally prevents incomplete Italian
# sources from reaching the generated site.
IT_PENDING_ALL = (
    'La traduzione italiana di questa diatriba non è ancora pronta. '
    'Qui sotto è riportata la traduzione inglese di George Long (1890).'
)
IT_PENDING_SOME = (
    'Traduzione italiana in corso: le sezioni non ancora tradotte '
    'mostrano il testo greco.'
)
IT_PENDING_TITLE = 'Il titolo di questa diatriba non è ancora tradotto.'

ROOT_HOME_TITLE = 'Epitteto, Diatribe — italiano, inglese e greco antico'
ROOT_HOME_DESCRIPTION = (
    'Le Diatribe di Epitteto in tre edizioni complete: traduzione italiana, '
    'traduzione inglese di George Long e testo greco di Schenkl.'
)

GENERATED_FILE_NOTE = '''<!--
FILE GENERATO. NON MODIFICARE A MANO.

Modificare invece:
- translation/it/**.md      per il testo e i titoli italiani
- data/intro.json           per le note introduttive delle home page
- tools/site_config.py      per lingue, testi dell'interfaccia, URL
- styles.css                per l'aspetto grafico

Poi eseguire:
    run.bat
-->
'''


def diatribe_path(slug):
    """Relative path of a diatribe page inside a language subtree."""
    return f'{DIATRIBE_DIR}/{slug}'


def pages_list(diatribes):
    """Every page that exists in all three languages, as HTML page paths."""
    return ['index.html', 'credits.html'] + [
        f'{diatribe_path(d["slug"])}.html' for d in diatribes
    ]
