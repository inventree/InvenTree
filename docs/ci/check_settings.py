"""Check that the global / user settings macros expanded correctly in the built documentation.

For every '{{ globalsetting(...) }}' and '{{ usersetting(...) }}' macro call in
the markdown sources, the rendered page is checked against the setting
definitions exported from the backend (docs/generated/inventree_settings.json):

- The setting key exists
- Full form: a settings table row is rendered, with the expected name,
  description, default value and units
- Short form ('short=True'): an inline reference with the expected name is rendered
- The page contains no macro rendering errors

Usage:
    python docs/ci/check_settings.py [--site-dir <path>]
"""

import json
from pathlib import Path

from docs_checks import (
    GENERATED_DIR,
    Checker,
    MacroCall,
    Page,
    check_macro_errors,
    find_macro_calls,
    iter_pages,
    normalize,
    run,
    table_row,
)

SETTINGS_FILE = GENERATED_DIR / 'inventree_settings.json'

# Macro name -> settings group in the exported settings file
MACROS = {'globalsetting': 'global', 'usersetting': 'user'}

# Expected header of a table containing settings (as rendered by the 'rendersetting' macro)
TABLE_HEADERS = ['Name', 'Description', 'Default', 'Units']


def check_code_cell(cell, expected, label: str, checker: Checker):
    """Check a table cell which should contain a value rendered as code (or be empty)."""
    text = cell.get_text().strip()

    if expected:
        code = cell.find('code')
        checker.check(
            code is not None and code.get_text().strip() == str(expected).strip(),
            f'{label} expected "{expected}", found "{text}"',
        )
    else:
        checker.check(not text, f'{label} expected to be empty, found "{text}"')


def check_full(page: Page, call: MacroCall, key: str, setting: dict, checker):
    """Check the rendered table row for a (full) setting macro call."""
    label = f'{page.label}:{call.line} {call.name}("{key}")'

    elements = page.soup.select(f'div[title="{key}"]')

    if not checker.check(bool(elements), f'{label} not rendered'):
        return

    row = table_row(elements[0])

    if not checker.check(row is not None, f'{label} not rendered within a table'):
        return

    checker.check(
        row.headers == TABLE_HEADERS,
        f'{label} rendered in a table with unexpected headers {row.headers}',
    )

    if not checker.check(
        len(row.cells) == len(TABLE_HEADERS),
        f'{label} row has {len(row.cells)} columns (expected {len(TABLE_HEADERS)})',
    ):
        return

    name, description, default, units = row.cells

    # Names / descriptions may contain markdown (e.g. `code`), so compare loosely
    checker.check(
        normalize(name.get_text(' ')) == normalize(setting['name']),
        f'{label} name: expected "{setting["name"]}", found "{name.get_text(" ", strip=True)}"',
    )
    checker.check(
        normalize(description.get_text(' ')) == normalize(setting['description']),
        f'{label} description: expected "{setting["description"]}", found "{description.get_text(" ", strip=True)}"',
    )

    expected_default = call.arg(2, 'default') or setting.get('default')

    check_code_cell(default, expected_default, f'{label} default:', checker)
    check_code_cell(units, setting.get('units'), f'{label} units:', checker)


def check_short(page: Page, call: MacroCall, key: str, setting: dict, checker):
    """Check the rendered inline reference for a (short) setting macro call."""
    label = f'{page.label}:{call.line} {call.name}("{key}", short=True)'

    names = [
        normalize(span.get_text(' '))
        for span in page.soup.select(f'span[title="{key}"]')
    ]

    checker.check(
        normalize(setting['name']) in names,
        f'{label} expected inline reference "{setting["name"]}", found {names}',
    )


def check_settings(site_dir: Path, checker: Checker):
    """Check all global / user setting macro calls against the rendered documentation."""
    with open(SETTINGS_FILE, encoding='utf-8') as f:
        settings = json.load(f)

    counts = dict.fromkeys(MACROS, 0)

    for page in iter_pages(site_dir):
        page_calls = []

        for macro in MACROS:
            calls, skipped = find_macro_calls(page, macro)
            counts[macro] += len(calls)
            page_calls.extend(calls)

            checker.check(
                skipped == 0,
                f'{page.label}: {skipped} {macro}() calls with non-literal arguments cannot be checked',
            )

        if not page_calls:
            continue

        if not checker.check(
            page.output.exists(), f'{page.label}: Missing rendered page {page.output}'
        ):
            continue

        check_macro_errors(page, checker)

        for call in page_calls:
            group = MACROS[call.name]
            key = call.arg(0, 'key')
            setting = settings.get(group, {}).get(key)

            if not checker.check(
                setting is not None,
                f'{page.label}:{call.line} {call.name}("{key}"): unknown {group} setting',
            ):
                continue

            if call.arg(1, 'short', False):
                check_short(page, call, key, setting, checker)
            else:
                check_full(page, call, key, setting, checker)

    for macro, count in counts.items():
        checker.check(count > 0, f'No {macro}() macro calls found in documentation')

    print(
        '  Checked '
        + ', '.join(f'{count} {macro}() calls' for macro, count in counts.items())
    )


if __name__ == '__main__':
    run('Checking global and user settings macros', check_settings)
