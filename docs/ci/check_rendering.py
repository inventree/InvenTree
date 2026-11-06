"""Check every page of the built documentation for unexpanded or broken markup.

Problems in the markdown sources (or in macro expansion) often do not fail the
mkdocs build, but instead leave raw markup in the rendered page. This script
scans the body text of every rendered page (ignoring code blocks) for:

- Macro rendering errors inserted by mkdocs-macros
- Unexpanded jinja markup from the markdown source, e.g. '{{ config.extra.unknown_variable }}'
  (mkdocs-macros leaves undefined variables in place, rather than failing)
- Markdown table rows rendered as a paragraph (e.g. separated from their table by a blank line)
- Admonitions / collapsible blocks / content tabs which were not rendered
- mkdocstrings directives which were not rendered

Usage:
    python docs/ci/check_rendering.py [--site-dir <path>]
"""

import re
from pathlib import Path

from docs_checks import Checker, check_macro_errors, iter_pages, run

# Unexpanded jinja expressions / statements
JINJA_RE = re.compile(r'{{.*?}}|{%.*?%}', re.DOTALL)

# Paragraph-level patterns which indicate a block element was not rendered
PARAGRAPH_PATTERNS = {
    'markdown table row': re.compile(r'^\|.*\|.*\|', re.MULTILINE),
    'admonition': re.compile(r'^!!!\s', re.MULTILINE),
    'collapsible block': re.compile(r'^\?\?\?\+?\s', re.MULTILINE),
    'content tab': re.compile(r'^===\+?\s+"', re.MULTILINE),
    'mkdocstrings directive': re.compile(r'^:::\s', re.MULTILINE),
}

# Elements whose content is not checked (code is expected to contain raw markup)
IGNORED_ELEMENTS = ['pre', 'code', 'script', 'style', 'kbd']


def squash(text: str) -> str:
    """Remove all whitespace, for comparing markup between source and rendered text."""
    return re.sub(r'\s+', '', text)


def check_rendering(site_dir: Path, checker: Checker):
    """Check all rendered pages for unexpanded or broken markup."""
    total = 0

    for page in iter_pages(site_dir):
        if not checker.check(
            page.output.exists(), f'{page.label}: Missing rendered page {page.output}'
        ):
            continue

        total += 1

        check_macro_errors(page, checker)

        content = page.soup.select_one('article') or page.soup.body

        if content is None:
            checker.check(False, f'{page.label}: Page has no content')
            continue

        for element in content.find_all(IGNORED_ELEMENTS):
            element.decompose()

        # Unexpanded jinja markup anywhere in the page text.
        # Only markup which is present in the (jinja-processed) markdown source is flagged,
        # as macro output may legitimately contain jinja-like text (e.g. Django template
        # tag docstrings). Markup within '{% raw %}' blocks is excluded from page.text.
        source_markup = {squash(m) for m in JINJA_RE.findall(page.text)}
        leftovers = [
            m
            for m in JINJA_RE.findall(content.get_text(' '))
            if squash(m) in source_markup
        ]
        checker.check(
            not leftovers,
            f'{page.label}: Unexpanded jinja markup: {[s[:60] for s in leftovers[:5]]}',
        )

        # Block elements which were rendered as plain paragraphs
        paragraphs = [p.get_text(' ', strip=True) for p in content.find_all('p')]

        for name, pattern in PARAGRAPH_PATTERNS.items():
            # Match at the start of any line, as the broken markup may follow other text
            # in the same paragraph (e.g. a table with no blank line before it)
            matches = [text for text in paragraphs if pattern.search(text)]
            checker.check(
                not matches,
                f'{page.label}: Unrendered {name}: {[text[:80] for text in matches[:3]]}',
            )

    checker.check(total > 0, 'No rendered pages found')
    print(f'  Checked {total} pages')


if __name__ == '__main__':
    run('Checking pages for unexpanded or broken markup', check_rendering)
