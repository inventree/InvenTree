"""WeasyPrint URL fetcher with security restrictions for report generation."""

import logging
from urllib.parse import urlparse

from weasyprint.urls import URLFetcher

logger = logging.getLogger('inventree')


class InvenTreeURLFetcher(URLFetcher):
    """WeasyPrint URL fetcher restricted to safe origins."""

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
