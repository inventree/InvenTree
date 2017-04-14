from django.conf.urls import url

from . import views

urlpatterns = [
    # Manufacturer detail
    url(r'^(?P<pk>[0-9]+)/?$', views.ManufacturerDetail.as_view(), name='manufacturer-detail'),

    # List manufacturers
    url(r'^\?.*/?$', views.ManufacturerList.as_view()),
    url(r'^$', views.ManufacturerList.as_view())
]
