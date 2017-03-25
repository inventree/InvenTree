from django.conf.urls import url

from . import views

urlpatterns = [
    # Display part detail
    url(r'^(?P<part_id>[0-9]+)/$', views.partdetail, name='detail'),
    
    # Display a part category
    url(r'^category/(?P<category_id>[0-9]+)/$', views.category, name='category'),
    url(r'^$', views.index, name='index')
]