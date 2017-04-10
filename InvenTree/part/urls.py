from django.conf.urls import url

from . import views

urlpatterns = [
    # part landing page
    url(r'^$', views.part_index),

    # part category landing page
    url(r'^category/$', views.category_index)
]
