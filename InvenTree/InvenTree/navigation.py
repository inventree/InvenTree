from django.utils.translation import gettext_lazy as _, pgettext_lazy
from django.urls import reverse

from common.signals import (
	nav_topbar
)

def get_global_navigation(request):
    url = request.resolver_match
    roles = request._roles
    if not url:
        return []

    nav = [
        {
            'label': _('Parts'),
            'url': reverse('part-index'),
            'active': 'part' in url.url_name,
            'icon': 'fas fa-shapes',
        },
        {
            'label': _('Stock'),
            'url': reverse('stock-index'),
            'active': 'events' in url.url_name,
            'icon': 'fas fa-boxes',
        },
        {
            'label': _('Build'),
            'url': reverse('build-index'),
            'active': 'organizers' in url.url_name,
            'icon': 'fas fa-tools',
        }
    ]
    if roles['purchase_order']['view']:
        nav.append({
            'label': _('Buy'),
#            'url': reverse('control:users'),
            'active': False,
            'icon': 'fas fa-shopping-cart',
            'children': [
                {
                    'label': _('Suppliers'),
                    'url': reverse('supplier-index'),
                    'active': ('users' in url.url_name),
                    'icon': 'fas fa-building',
                },
                {
                    'label': _('Manufacturers'),
                    'url': reverse('manufacturer-index'),
                    'active': ('sudo' in url.url_name),
                    'icon': 'fas fa-industry',
                },
                {
                    'label': _('Purchase Orders'),
                    'url': reverse('po-index'),
                    'active': ('sudo' in url.url_name),
                    'icon': 'fas fa-list',
                },
            ]
        })

    if roles['sales_order']['view']:
        nav.append({
            'label': _('Sell'),
#            'url': reverse('control:users'),
            'active': False,
            'icon': 'fas fa-truck',
            'children': [
                {
                    'label': _('Customers'),
                    'url': reverse('customer-index'),
                    'active': ('users' in url.url_name),
                    'icon': 'fas fa-user-tie',
                },
                {
                    'label': _('Sales Orders'),
                    'url': reverse('so-index'),
                    'active': ('sudo' in url.url_name),
                    'icon': 'fas fa-list',
                },
            ]
        })

    merge_in(nav, sorted(
        sum((list(a[1]) for a in nav_topbar.send(request, request=request)), []),
        key=lambda r: (1 if r.get('parent') else 0, r['label'])
    ))
    return nav


def merge_in(nav, newnav):
    for item in newnav:
        if 'parent' in item:
            parents = [n for n in nav if n['url'] == item['parent']]
            if parents:
                if 'children' not in parents[0]:
                    parents[0]['children'] = []
                parents[0]['children'].append(item)
        else:
            nav.append(item)
