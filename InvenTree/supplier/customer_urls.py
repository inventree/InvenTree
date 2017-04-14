from django.conf.urls import url, include

from . import views

urlpatterns = [
    # Customer detail
    url(r'^(?P<pk>[0-9]+)/?$', views.CustomerDetail.as_view(), name='customer-detail'),

    # List customers
    url(r'^\?.*/?$', views.CustomerList.as_view()),
    url(r'^$', views.CustomerList.as_view())
]
