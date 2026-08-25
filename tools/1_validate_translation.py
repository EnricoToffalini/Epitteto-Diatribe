"""Validate the completed Italian edition without modifying its source files."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from site_config import ROOT
import translation_store


def main():
    data = json.loads((ROOT / 'data' / 'discourses.json').read_text(encoding='utf-8'))
    diatribes = data['diatribes']
    translations = translation_store.load_all(diatribes)
    errors = []

    for diatribe in diatribes:
        slug = diatribe['slug']
        entry = translations.get(slug, {})
        if not translation_store.path_for(slug).exists():
            errors.append(f'{slug}: file mancante')
            continue
        if not entry.get('title'):
            errors.append(f'{slug}: titolo italiano mancante')
        translated = entry.get('sections', {})
        missing = [str(section['n']) for section in diatribe['sections']
                   if not translated.get(section['n'])]
        if missing:
            errors.append(f'{slug}: sezioni mancanti: {", ".join(missing)}')

    if errors:
        print('Testo italiano incompleto:')
        for error in errors:
            print(f'  - {error}')
        return 1

    done, total, complete = translation_store.progress(diatribes, translations)
    print(f'  testo italiano completo: {done}/{total} sezioni, '
          f'{len(complete)}/{len(diatribes)} diatribe.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
