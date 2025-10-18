"""URLs for web app."""

from django.conf import settings
from django.urls import include, path, re_path
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import RedirectView, TemplateView

spa_view = ensure_csrf_cookie(TemplateView.as_view(template_name='web/index.html'))


def cui_compatibility_urls(base: str) -> list:
    """Generate a list of URL patterns for compatibility with old (CUI) URLs.

    These URLs are provided for backwards compatibility with older versions of InvenTree,
    before we moved to a SPA (Single Page Application) architecture in the 1.0.0 release.

    At some future point these may be removed?

    Args:
        base (str): The base URL to use for generating the patterns.

    Returns:
        list: A list of URL patterns.
    """
    return [
        # Old 'index' view - reroute to the dashboard
        path('index/', RedirectView.as_view(url=f'/{base}')),
        path('settings/', RedirectView.as_view(url=f'/{base}/settings')),
        # Company patterns
        path(
            'company/',
            include([
                path(
                    'customers/',
                    RedirectView.as_view(url=f'/{base}/sales/index/customers'),
                ),
                path(
                    'manufacturers/',
                    RedirectView.as_view(url=f'/{base}/purchasing/index/manufacturers'),
                ),
                path(
                    'suppliers/',
                    RedirectView.as_view(url=f'/{base}/purchasing/index/suppliers'),
                ),
                re_path(
                    r'(?P<pk>\d+)/', RedirectView.as_view(url=f'/{base}/company/%(pk)s')
                ),
            ]),
        ),
        # "Part" app views
        re_path(
            r'^part/(?P<path>.*)$', RedirectView.as_view(url=f'/{base}/part/%(path)s')
        ),
        # "Stock" app views
        re_path(
            r'^stock/(?P<path>.*)$', RedirectView.as_view(url=f'/{base}/stock/%(path)s')
        ),
        # "Build" app views (requires some custom handling)
        path(
            'build/',
            include([
                re_path(
                    r'^(?P<pk>\d+)/',
                    RedirectView.as_view(
                        url=f'/{base}/manufacturing/build-order/%(pk)s'
                    ),
                ),
                re_path('.*', RedirectView.as_view(url=f'/{base}/manufacturing/')),
            ]),
        ),
        # "Order" app views
        path(
            'order/',
            include([
                path(
                    'purchase-order/',
                    include([
                        re_path(
                            r'^(?P<pk>\d+)/',
                            RedirectView.as_view(
                                url=f'/{base}/purchasing/purchase-order/%(pk)s'
                            ),
                        ),
                        re_path(
                            '.*',
                            RedirectView.as_view(
                                url=f'/{base}/purchasing/index/purchaseorders/'
                            ),
                        ),
                    ]),
                ),
                path(
                    'sales-order/',
                    include([
                        re_path(
                            r'^(?P<pk>\d+)/',
                            RedirectView.as_view(
                                url=f'/{base}/sales/sales-order/%(pk)s'
                            ),
                        ),
                        re_path(
                            '.*',
                            RedirectView.as_view(
                                url=f'/{base}/sales/index/salesorders/'
                            ),
                        ),
                    ]),
                ),
                path(
                    'return-order/',
                    include([
                        re_path(
                            r'^(?P<pk>\d+)/',
                            RedirectView.as_view(
                                url=f'/{base}/sales/return-order/%(pk)s'
                            ),
                        ),
                        re_path(
                            '.*',
                            RedirectView.as_view(
                                url=f'/{base}/sales/index/returnorders/'
                            ),
                        ),
                    ]),
                ),
            ]),
        ),
    ]


urlpatterns = [
    path(
        f'{settings.FRONTEND_URL_BASE}/',
        include([
            path(
                'set-password?uid=<uid>&token=<token>',
                spa_view,
                name='password_reset_confirm',
            ),
            re_path('.*', spa_view, name='web-wildcard'),
        ]),
    ),
    path(settings.FRONTEND_URL_BASE, spa_view, name='web'),
]
