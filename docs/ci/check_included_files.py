"""Check that files included via the includefile() / templatefile() macros rendered correctly.

These macros insert the contents of a source file into the page, inside a
collapsible '??? abstract' block. The block relies on correct indentation in
the markdown source, so it can silently break (e.g. if the macro call itself
is indented, or placed inside a list).

For every macro call in the markdown sources:

- The included file exists
- A collapsible block with the expected title is rendered
- The block contains a code block whose content matches the source file

Usage:
    python docs/ci/check_included_files.py [--site-dir <path>]
"""

from pathlib import Path, PurePosixPath

from docs_checks import (
    REPO_DIR,
    Checker,
    MacroCall,
    Page,
    check_macro_errors,
    find_macro_calls,
    iter_pages,
    run,
)

# Directory containing report / label templates (as used by the templatefile macro)
TEMPLATE_DIR = PurePosixPath('src', 'backend', 'InvenTree', 'report', 'templates')


def content_lines(text: str) -> list[str]:
    """Return the lines of a file / code block, ignoring trailing whitespace and blank edges."""
    return [line.rstrip() for line in text.strip('\n').splitlines()]


def resolve_call(call: MacroCall) -> tuple[str, str]:
    """Return the (repo relative filename, expected block title) for a macro call."""
    if call.name == 'templatefile':
        filename = call.arg(0, 'filename')
        return str(TEMPLATE_DIR / filename), f'Template: {PurePosixPath(filename).name}'

    return call.arg(0, 'filename'), call.arg(1, 'title')


def check_include(page: Page, call: MacroCall, checker: Checker):
    """Check the rendered output of a single includefile() / templatefile() call."""
    filename, title = resolve_call(call)
    label = f'{page.label}:{call.line} {call.name}("{call.arg(0, "filename")}")'

    path = (REPO_DIR / filename).resolve()

    # Only allow files within the repository
    if not checker.check(
        path.is_relative_to(REPO_DIR) and path.is_file(),
        f'{label} included file does not exist: {filename}',
    ):
        return

    blocks = [
        details
        for details in page.soup.select('details.abstract')
        if details.summary and details.summary.get_text(strip=True) == title
    ]

    if not checker.check(
        bool(blocks), f'{label} collapsible block "{title}" not rendered'
    ):
        return

    expected = content_lines(path.read_text(encoding='utf-8'))

    matches = [
        details
        for details in blocks
        if any(
            content_lines(pre.get_text()) == expected for pre in details.select('pre')
        )
    ]

    checker.check(
        bool(matches),
        f'{label} collapsible block "{title}" does not contain the content of {filename}',
    )


def check_included_files(site_dir: Path, checker: Checker):
    """Check all includefile() / templatefile() macro calls against the rendered documentation."""
    counts = {'includefile': 0, 'templatefile': 0}

    for page in iter_pages(site_dir):
        page_calls = []

        for macro in counts:
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
            check_include(page, call, checker)

    for macro, count in counts.items():
        checker.check(count > 0, f'No {macro}() macro calls found in documentation')

    print(
        '  Checked '
        + ', '.join(f'{count} {macro}() calls' for macro, count in counts.items())
    )


if __name__ == '__main__':
    run('Checking included source files', check_included_files)
