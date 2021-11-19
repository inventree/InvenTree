from django.conf.urls import url, include

from . import views

basket_urls = [
    url(r'^(?P<pk>\d+)/', include([
        url(r'^qr_code/?', views.BasketQRCode.as_view(), name='basket-qr'),
        url(r'^.*$',views.SOBasketDetail.as_view(), name='basket-details'),
    ])),
    url(r'^.*$', views.SOBasketIndex.as_view(), name='basket-index'),
]
