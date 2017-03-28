from django.conf.urls import url

from . import views

urlpatterns = [
    
    # Display details of a supplier
    url(r'^(?P<supplier_id>[0-9]+)/$', views.supplierDetail, name='detail'),
    
    url(r'^$', views.index, name='index')
]
