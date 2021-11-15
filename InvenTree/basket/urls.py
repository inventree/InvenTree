from django.conf.urls import url, include

from . import views

basket_urls = [
    url(r'^.*$', views.SOBasketIndex.as_view(), name='basket-index'),
]
