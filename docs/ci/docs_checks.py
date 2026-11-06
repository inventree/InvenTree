"""Shared helpers for the post-build documentation checks in this directory.

Each check_*.py script in this directory inspects the *built* documentation
site (e.g. on the readthedocs builder, after mkdocs has run), and compares
the rendered HTML against expected values derived from the markdown sources
and the generated data files.
"""

import argparse
import ast
import html
import os
import re
import sys
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

from bs4 import BeautifulSoup

CI_DIR = Path(__file__).resolve().parent
DOCS_DIR = CI_DIR.parent
REPO_DIR = DOCS_DIR.parent

# Markdown source directory (mkdocs 'docs_dir')
SOURCE_DIR = DOCS_DIR / 'docs'

# Generated data files (produced by 'invoke build-docs')
GENERATED_DIR = DOCS_DIR / 'generated'

# Backend source code (used by mkdocstrings)
BACKEND_DIR = REPO_DIR / 'src' / 'backend' / 'InvenTree'

# Text inserted into a page by mkdocs-macros when a macro fails to render
MACRO_ERROR_MARKERS = ('Macro Rendering Error', 'Macro Syntax Error')

# Jinja '{% raw %}' blocks are not rendered by mkdocs-macros
RAW_BLOCK_RE = re.compile(r'{%-?\s*raw\s*-?%}.*?{%-?\s*endraw\s*-?%}', re.DOTALL)


class Checker:
    """Collects check results, so that all failures are reported in one run."""

    def __init__(self):
        """Initialize the checker."""
        self.errors = []
        self.passed = 0

    def check(self, condition: bool, message: str) -> bool:
        """Record the result of a single check."""
        if condition:
            self.passed += 1
        else:
            self.errors.append(message)
        return condition

    def report(self) -> int:
        """Print a summary of the results, and return a process exit code."""
        print(f'{self.passed} checks passed, {len(self.errors)} checks failed')

        for error in self.errors:
            print(f'  FAIL: {error}')

        return 1 if self.errors else 0


@dataclass
class Page:
    """A markdown source page, and the location of its rendered HTML output."""

    source: Path
    output: Path
    text: str  # Markdown source, with '{% raw %}' blocks blanked out
    source_text: str = field(default='', repr=False)  # Unmodified markdown source
    _soup: BeautifulSoup | None = field(default=None, repr=False)

    @property
    def label(self) -> str:
        """Short label used in error messages."""
        return str(self.source.relative_to(SOURCE_DIR))

    @property
    def soup(self) -> BeautifulSoup:
        """Parsed HTML output for this page (cached)."""
        if self._soup is None:
            with open(self.output, encoding='utf-8') as f:
                self._soup = BeautifulSoup(f.read(), 'html.parser')
        return self._soup

    def line_of(self, offset: int) -> int:
        """Return the (1-indexed) line number of a character offset in the source text."""
        return self.text.count('\n', 0, offset) + 1


@dataclass
class MacroCall:
    """A literal macro invocation found in a markdown source file."""

    name: str
    args: list
    kwargs: dict
    line: int

    def arg(self, index: int, name: str, default=None):
        """Return a macro argument, by position or by keyword."""
        if name in self.kwargs:
            return self.kwargs[name]
        if index < len(self.args):
            return self.args[index]
        return default


def output_path(site_dir: Path, source: Path) -> Path:
    """Return the rendered HTML file for a markdown source file.

    Assumes 'use_directory_urls: true' (as set in mkdocs.yml).
    """
    rel = source.relative_to(SOURCE_DIR).with_suffix('')

    if rel.name in ('index', 'README'):
        return site_dir / rel.parent / 'index.html'

    return site_dir / rel / 'index.html'


def iter_pages(site_dir: Path) -> Iterator[Page]:
    """Iterate over all markdown source pages.

    Yields:
        Page: Each markdown source page, with the location of its rendered output.
    """
    for source in sorted(SOURCE_DIR.rglob('*.md')):
        with open(source, encoding='utf-8') as f:
            source_text = f.read()

        # Blank out raw blocks (not rendered by mkdocs-macros), keeping line numbers intact
        text = RAW_BLOCK_RE.sub(lambda m: '\n' * m.group(0).count('\n'), source_text)

        yield Page(
            source=source,
            output=output_path(site_dir, source),
            text=text,
            source_text=source_text,
        )


def find_macro_calls(page: Page, name: str) -> tuple[list[MacroCall], int]:
    """Find all invocations of the named macro in a page.

    Returns a tuple of (literal_calls, skipped), where 'skipped' is the number
    of invocations whose arguments are not plain literals (e.g. jinja variables),
    and so cannot be checked against expected values.
    """
    pattern = re.compile(
        r'{{-?\s*' + re.escape(name) + r'\s*\((.*?)\)\s*-?}}', re.DOTALL
    )

    calls = []
    skipped = 0

    for match in pattern.finditer(page.text):
        try:
            expr = ast.parse(f'f({match.group(1)})', mode='eval').body
            args = [ast.literal_eval(a) for a in expr.args]
            kwargs = {k.arg: ast.literal_eval(k.value) for k in expr.keywords}
        except (SyntaxError, ValueError):
            skipped += 1
            continue

        calls.append(MacroCall(name, args, kwargs, page.line_of(match.start())))

    return calls, skipped


def normalize(text: str) -> str:
    """Normalize text for loose comparison between markdown source and rendered HTML.

    Removes markup, punctuation and whitespace differences, so that (for example)
    '`foo` *bar*' in markdown matches '<code>foo</code> <em>bar</em>' in HTML.
    """
    text = html.unescape(text or '')
    text = re.sub(r'<[^>]+>', ' ', text)
    return ' '.join(re.findall(r'[a-z0-9]+', text.lower()))


@dataclass
class TableRow:
    """A rendered table row containing a particular element."""

    cells: list  # <td> elements in the row
    headers: list[str]  # Header text of the enclosing table


def table_row(element) -> TableRow | None:
    """Return the table row which contains the provided element (or None if not in a table)."""
    if element.find_parent('td') is None:
        return None

    row = element.find_parent('tr')
    table = element.find_parent('table')

    if row is None or table is None:
        return None

    headers = [th.get_text(' ', strip=True) for th in table.select('thead th')]

    return TableRow(cells=row.find_all('td', recursive=False), headers=headers)


def check_macro_errors(page: Page, checker: Checker):
    """Check that no macro rendering errors were inserted into a rendered page."""
    text = page.soup.get_text(' ')

    for marker in MACRO_ERROR_MARKERS:
        checker.check(
            marker not in text, f'{page.label}: Page contains a "{marker}" block'
        )


def default_site_dir() -> Path:
    """Determine the default location of the built documentation."""
    rtd_output = os.environ.get('READTHEDOCS_OUTPUT')

    if rtd_output:
        return Path(rtd_output) / 'html'

    return DOCS_DIR / 'site'


def run(description: str, check: Callable[[Path, Checker], None]):
    """Parse command line arguments, run a check function, and exit with the result."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        '--site-dir',
        type=Path,
        default=None,
        help='Directory containing the built documentation (default: $READTHEDOCS_OUTPUT/html or docs/site)',
    )
    args = parser.parse_args()

    site_dir = (args.site_dir or default_site_dir()).resolve()

    print(f'{description}')
    print(f'Checking built documentation in: {site_dir}')

    if not site_dir.is_dir():
        print(f'ERROR: Site directory does not exist: {site_dir}')
        sys.exit(1)

    checker = Checker()
    check(site_dir, checker)

    sys.exit(checker.report())
