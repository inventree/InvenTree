from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^(?P<pk>[0-9]+)/?$', views.SupplierPartDetail.as_view(), name='supplierpart-detail'),

    url(r'^\?.*/?$', views.SupplierPartList.as_view()),
    url(r'^$', views.SupplierPartList.as_view())
]
