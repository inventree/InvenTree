from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^(?P<pk>[0-9]+)/?$', views.SupplierPriceBreakDetail.as_view(), name='supplierpricebreak-detail'),

    url(r'^\?.*/?$', views.SupplierPriceBreakList.as_view()),
    url(r'^$', views.SupplierPriceBreakList.as_view())
]
