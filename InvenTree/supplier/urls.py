from django.conf.urls import url, include

from . import views

partpatterns = [
    url(r'^(?P<pk>[0-9]+)/?$', views.SupplierPartDetail.as_view(), name='supplier-part-detail'),

    url(r'^\?.*/?$', views.SupplierPartList.as_view()),
    url(r'^$', views.SupplierPartList.as_view())
]

pricepatterns = [
    url(r'^(?P<pk>[0-9]+)/?$', views.SupplierPriceBreakDetail.as_view(), name='price-break-detail'),

    url(r'^\?.*/?$', views.SupplierPriceBreakList.as_view()),
    url(r'^$', views.SupplierPriceBreakList.as_view())
]

urlpatterns = [

    # Supplier part information
    url(r'part/?', include(partpatterns)),

    # Supplier price information
    url(r'price/?', include(pricepatterns)),

    # Display details of a supplier
    url(r'^(?P<pk>[0-9]+)/?$', views.SupplierDetail.as_view(), name='supplier-detail'),

    # List suppliers
    url(r'^\?.*/?$', views.SupplierList.as_view()),
    url(r'^$', views.SupplierList.as_view())
]
