"""Check that integrated source code documentation (mkdocstrings) rendered correctly.

For every '::: <python.object.path>' directive in the markdown sources, the
referenced object is resolved statically from the backend source code (using
griffe, as mkdocstrings does), and the corresponding rendered block is checked:

- One top-level documentation block is rendered per directive, in order
- The block is of the expected kind (class / function / attribute / module)
- The docstring summary and documented parameters appear in the block
- Where source code is shown, it is from the expected file and defines the object

Usage:
    python docs/ci/check_mkdocstrings.py [--site-dir <path>]
"""

import logging
import re
import textwrap
from pathlib import Path

import griffe
import yaml
from docs_checks import BACKEND_DIR, Checker, Page, iter_pages, normalize, run

DIRECTIVE_RE = re.compile(r'^:::\s+(\S+)\s*$')
FENCE_RE = re.compile(r'^\s*(```|~~~)')
RAW_TAG_RE = re.compile(r'{%-?\s*(end)?raw\s*-?%}')

# mkdocstrings-python defaults for the options which affect these checks
DEFAULT_OPTIONS = {
    'show_source': True,
    'show_docstring_description': True,
    'show_docstring_parameters': True,
}


class Directive:
    """A '::: identifier' directive in a markdown file."""

    def __init__(self, identifier: str, options: dict, line: int):
        """Initialize the directive."""
        self.identifier = identifier
        self.options = options
        self.line = line

    def option(self, name: str) -> bool:
        """Return the value of a (boolean) rendering option for this directive."""
        return bool(self.options.get(name, DEFAULT_OPTIONS[name]))


def find_directives(page: Page) -> list[Directive]:
    """Find all mkdocstrings directives in a page (ignoring fenced code blocks)."""
    # Use the unmodified source (so that code fences are tracked correctly),
    # but remove the jinja raw tags, as they are removed before markdown rendering
    lines = RAW_TAG_RE.sub('', page.source_text).splitlines()
    directives = []
    in_fence = False
    idx = 0

    while idx < len(lines):
        line = lines[idx]

        if FENCE_RE.match(line):
            in_fence = not in_fence

        match = None if in_fence else DIRECTIVE_RE.match(line)

        if not match:
            idx += 1
            continue

        # Collect the indented YAML configuration block which follows the directive
        start = idx
        idx += 1
        block = []

        while idx < len(lines) and (not lines[idx].strip() or lines[idx][0] in ' \t'):
            block.append(lines[idx])
            idx += 1

        config = yaml.safe_load(textwrap.dedent('\n'.join(block))) or {}
        options = config.get('options') or {}

        directives.append(Directive(match.group(1), options, start + 1))

    return directives


class Resolver:
    """Statically resolve python object paths from the backend source code."""

    def __init__(self):
        """Initialize the griffe loader."""
        logging.getLogger('griffe').setLevel(logging.ERROR)
        self.loader = griffe.GriffeLoader(search_paths=[str(BACKEND_DIR)])

    def resolve(self, identifier: str):
        """Return the griffe object for the provided identifier, or None."""
        parts = identifier.split('.')

        # Find the longest importable module prefix, then walk the members
        for n in range(len(parts), 0, -1):
            try:
                obj = self.loader.load('.'.join(parts[:n]))
            except (ImportError, griffe.GriffeError):
                continue

            try:
                for name in parts[n:]:
                    obj = obj.members[name]
                return obj.final_target if obj.is_alias else obj
            except (KeyError, griffe.AliasResolutionError):
                return None

        return None


def docstring_summary(obj) -> str:
    """Return the first paragraph of the object's docstring text (if any)."""
    if not obj.docstring:
        return ''

    sections = obj.docstring.parse('google')

    if sections and sections[0].kind.value == 'text':
        return sections[0].value.split('\n\n')[0]

    return ''


def docstring_parameters(obj) -> list[str]:
    """Return the names of parameters documented in the object's docstring."""
    if not obj.docstring:
        return []

    return [
        param.name
        for section in obj.docstring.parse('google')
        if section.kind.value == 'parameters'
        for param in section.value
    ]


def top_level_blocks(page: Page) -> list:
    """Return the top-level mkdocstrings blocks rendered on a page, in order."""
    return [
        div
        for div in page.soup.select('div.doc.doc-object')
        if not div.find_parent('div', class_='doc-object')
    ]


def check_block(page: Page, directive: Directive, obj, block, checker: Checker):
    """Check a single rendered mkdocstrings block against the source object."""
    label = f'{page.label}:{directive.line} [{directive.identifier}]'
    kind = obj.kind.value

    checker.check(
        f'doc-{kind}' in block.get('class', []),
        f'{label} Expected a "{kind}" block, found classes {block.get("class")}',
    )

    contents = block.select_one('div.doc-contents')

    if not checker.check(contents is not None, f'{label} Block has no contents'):
        return

    # Exclude the source listing from the docstring text comparison
    source = contents.select_one('details.mkdocstrings-source')
    text = normalize(
        contents.get_text(' ')
        if source is None
        else contents.get_text(' ').replace(source.get_text(' '), '')
    )

    summary = normalize(docstring_summary(obj))

    if summary and directive.option('show_docstring_description'):
        checker.check(
            summary in text, f'{label} Docstring summary not rendered: "{summary}"'
        )

    params = (
        docstring_parameters(obj)
        if directive.option('show_docstring_parameters')
        else []
    )

    for param in params:
        checker.check(
            normalize(param) in text,
            f'{label} Documented parameter not rendered: "{param}"',
        )

    if not directive.option('show_source'):
        return

    if not checker.check(source is not None, f'{label} Source code not rendered'):
        return

    filename = source.select_one('summary code')
    expected_file = Path(obj.filepath).resolve().relative_to(BACKEND_DIR).as_posix()

    checker.check(
        filename is not None and filename.get_text().strip().endswith(expected_file),
        f'{label} Source code is not from expected file "{expected_file}"',
    )

    keyword = {'class': 'class', 'function': 'def'}.get(kind)

    if keyword:
        checker.check(
            normalize(f'{keyword} {obj.name}') in normalize(source.get_text(' ')),
            f'{label} Rendered source code does not define "{keyword} {obj.name}"',
        )


def check_mkdocstrings(site_dir: Path, checker: Checker):
    """Check all mkdocstrings directives against the rendered documentation."""
    resolver = Resolver()
    total = 0

    for page in iter_pages(site_dir):
        directives = find_directives(page)

        if not directives:
            continue

        total += len(directives)

        if not checker.check(
            page.output.exists(), f'{page.label}: Missing rendered page {page.output}'
        ):
            continue

        blocks = top_level_blocks(page)

        checker.check(
            len(blocks) == len(directives),
            f'{page.label}: Expected {len(directives)} rendered code documentation blocks, found {len(blocks)}',
        )

        # Count mismatch is reported above - still check the blocks that do pair up
        for directive, block in zip(directives, blocks, strict=False):
            obj = resolver.resolve(directive.identifier)

            if checker.check(
                obj is not None,
                f'{page.label}:{directive.line} Cannot resolve "{directive.identifier}"',
            ):
                check_block(page, directive, obj, block, checker)

    checker.check(total > 0, 'No mkdocstrings directives found in documentation')
    print(f'  Checked {total} mkdocstrings directives')


if __name__ == '__main__':
    run('Checking integrated source code documentation', check_mkdocstrings)
