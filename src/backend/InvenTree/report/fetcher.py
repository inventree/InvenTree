"""WeasyPrint URL fetcher with security restrictions for report generation."""

import logging
from urllib.parse import urlparse

from weasyprint.urls import URLFetcher

logger = logging.getLogger('inventree')


class InvenTreeURLFetcher(URLFetcher):
    """WeasyPrint URL fetcher restricted to safe origins.

    Permitted:
    - ``data:`` URIs — self-contained, no network access.
    - ``http`` / ``https`` to the InvenTree server's own origin only (prevents SSRF).

    Blocked:
    - ``file://`` — all media and static assets must be inlined as ``data:`` URIs
      before the HTML reaches WeasyPrint; see the ``asset`` and ``uploaded_image``
      template tags.
    - All other schemes.
    """

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
