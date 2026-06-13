"""WeasyPrint URL fetcher with security restrictions for report generation."""

import logging
from urllib.parse import urlparse

from weasyprint.urls import URLFetcher

logger = logging.getLogger('inventree')


class InvenTreeURLFetcher(URLFetcher):
    """WeasyPrint URL fetcher restricted to safe origins."""

    def __init__(self, **kwargs):
        """Disable redirect following so a same-origin URL cannot be used for SSRF."""
        kwargs.setdefault('allow_redirects', False)
        super().__init__(**kwargs)

    def fetch(self, url, headers=None):
        """Validate *url* before delegating to the parent fetcher."""
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()

        if scheme in ('data', 'http', 'https'):
            self._validate_http_url(url, parsed)
            return super().fetch(url, headers)

        if scheme == 'file':
            logger.warning("InvenTreeURLFetcher: blocked file:// URL: '%s'", url)
            raise ValueError(
                f'file:// URLs are not permitted in report templates: {url}'
            )

        raise ValueError(f"URL scheme '{scheme}' is not permitted in report templates")

    def _validate_http_url(self, url: str, parsed) -> None:
        """Raise if HTTP/HTTPS fetching is disabled or the URL is an SSRF risk."""
        from common.settings import get_global_setting
        from InvenTree.helpers_model import validate_url_no_ssrf

        if not parsed.netloc:
            # data: URIs — self-contained, no network access required.
            return

        if not get_global_setting('REPORT_FETCH_URLS', cache=False):
            logger.warning(
                "InvenTreeURLFetcher: blocked URL '%s': remote fetching is disabled (REPORT_FETCH_URLS=False)",
                url,
            )
            raise ValueError(
                f'Remote URL fetching is disabled in report templates: {url}'
            )

        try:
            validate_url_no_ssrf(url)
        except ValueError:
            logger.warning(
                "InvenTreeURLFetcher: blocked URL '%s': resolves to a private or reserved address",
                url,
            )
            raise
