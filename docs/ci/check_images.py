"""Check that the 'image' macro expanded correctly in the built documentation.

For every '{{ image(...) }}' macro call in the markdown sources:

- The rendered page contains no macro rendering errors
- One image figure is rendered per macro call
- Each call renders a figure for the expected image file, with a consistent
  zoom link / overlay pair and alt text

For every rendered image figure:

- The image URL uses the expected assets base path for this build
  (e.g. '/en/latest/assets/' on readthedocs), and resolves to a non-empty
  file in the built site

Usage:
    python docs/ci/check_images.py [--site-dir <path>]
"""

import os
import posixpath
from pathlib import Path

from docs_checks import (
    Checker,
    MacroCall,
    Page,
    check_macro_errors,
    find_macro_calls,
    iter_pages,
    run,
)

FIGURE_SELECTOR = 'figure.image-inventree'


def expected_assets_base() -> str:
    """Return the URL base path for image assets (must match docs/main.py)."""
    rtd_version = os.environ.get('READTHEDOCS_VERSION')
    rtd_language = os.environ.get('READTHEDOCS_LANGUAGE')

    if rtd_version and rtd_language:
        return f'/{rtd_language}/{rtd_version}/assets/'

    return '/assets/'


def expected_src(call: MacroCall) -> str:
    """Return the expected image URL (relative to the assets base) for a macro call."""
    source = call.arg(0, 'source')

    if source.startswith('http'):
        return source

    base = call.arg(4, 'base', '') or ''

    return posixpath.normpath(posixpath.join('images', base, source))


def check_figure(page: Page, figure, site_dir: Path, checker: Checker) -> str:
    """Check a single rendered image figure. Returns the image URL."""
    img = figure.select_one('img.img-inline')
    label = f'{page.label}: Image'

    if not checker.check(img is not None, f'{label} figure has no inline <img>'):
        return ''

    src = img.get('src', '')
    label = f'{page.label}: Image "{src}"'

    checker.check(bool(img.get('alt')), f'{label} has no alt text')

    # The zoom link must point to the overlay, which shows the same image
    link = img.find_parent('a')
    overlay = figure.select_one('a.overlay')

    if checker.check(
        link is not None and overlay is not None,
        f'{label} is missing zoom link or overlay',
    ):
        checker.check(
            link.get('href') == f'#{overlay.get("id")}',
            f'{label} zoom link "{link.get("href")}" does not match overlay id "{overlay.get("id")}"',
        )

        overlay_img = overlay.select_one('img')
        checker.check(
            overlay_img is not None and overlay_img.get('src') == src,
            f'{label} overlay does not show the same image',
        )

    if src.startswith('http'):
        return src

    base = expected_assets_base()

    if checker.check(
        src.startswith(base), f'{label} does not start with assets path "{base}"'
    ):
        target = site_dir / 'assets' / src[len(base) :]

        checker.check(
            target.is_file() and target.stat().st_size > 0,
            f'{label} does not resolve to a file in the built site: {target}',
        )

    return src


def check_images(site_dir: Path, checker: Checker):
    """Check all image macro calls against the rendered documentation."""
    total_calls = 0
    total_figures = 0

    for page in iter_pages(site_dir):
        calls, skipped = find_macro_calls(page, 'image')
        expected_count = len(calls) + skipped
        total_calls += expected_count

        if not page.output.exists():
            checker.check(
                expected_count == 0,
                f'{page.label}: Missing rendered page {page.output}',
            )
            continue

        # Pages without image macros may still contain figures (e.g. via includes)
        if expected_count == 0 and 'image-inventree' not in page.output.read_text(
            encoding='utf-8'
        ):
            continue

        figures = page.soup.select(FIGURE_SELECTOR)
        total_figures += len(figures)

        srcs = [check_figure(page, figure, site_dir, checker) for figure in figures]

        if expected_count == 0:
            continue

        check_macro_errors(page, checker)

        checker.check(
            len(figures) == expected_count,
            f'{page.label}: Expected {expected_count} rendered images, found {len(figures)}',
        )

        base = expected_assets_base()

        for call in calls:
            expected = expected_src(call)
            if not expected.startswith('http'):
                expected = base + expected

            checker.check(
                expected in srcs,
                f'{page.label}:{call.line} image("{call.arg(0, "source")}") not rendered (expected src "{expected}")',
            )

    checker.check(total_calls > 0, 'No image macro calls found in documentation')
    print(f'  Checked {total_calls} image macro calls, {total_figures} rendered images')


if __name__ == '__main__':
    run('Checking image macros', check_images)
