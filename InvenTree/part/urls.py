from django.conf.urls import url

from . import views

urlpatterns = [
    # Display part detail
    url(r'^(?P<pk>[0-9]+)/$', views.PartDetail.as_view()),
    
    # Display a single part category
    url(r'^category/(?P<pk>[0-9]+)/$', views.PartCategoryDetail.as_view()),
    
    # Display a list of top-level categories
    url(r'^category/$', views.PartCategoryList.as_view()),
    
    # Display list of parts
    url(r'^$', views.PartList.as_view())
]
