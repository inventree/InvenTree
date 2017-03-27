from django.conf.urls import url

from . import views

urlpatterns = [
    # Display part detail
    url(r'^(?P<part_id>[0-9]+)/$', views.partDetail, name='detail'),
    
    # Display a list of top-level categories
    url(r'^category/$', views.categoryList, name='categorylist'),
    
    # Display a single part category
    url(r'^category/(?P<category_id>[0-9]+)/$', views.category, name='category'),
    url(r'^$', views.index, name='index')
]