from django.conf.urls import url

from . import views

bom_urls = [
    # Bom Item detail
    url(r'^(?P<pk>[0-9]+)/?$', views.BomItemDetail.as_view(), name='bomitem-detail'),

    # List of top-level categories
    url(r'^\?*.*/?$', views.BomItemList.as_view()),
    url(r'^$', views.BomItemList.as_view())
]