from django.conf.urls import url

from . import views

urlpatterns = [
    # Detail for a single stock item
    url(r'^(?P<pk>[0-9]+)/?$', views.StockDetail.as_view(), name='stockitem-detail'),

    # List all stock items, with optional filters
    url(r'^\?.*/?$', views.StockList.as_view()),
    url(r'^$', views.StockList.as_view()),
]
