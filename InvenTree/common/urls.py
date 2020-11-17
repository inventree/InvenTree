"""
URL lookup for common views
"""

from django.conf.urls import url, include
from django.urls import path


from . import views

task_urls = [
    url(r'^run/', views.run_task, name='task-run'),
    path('<uuid:pk>/', views.get_task, name='task-get'),
]

common_urls = [
    url(r'tasks/', include(task_urls)),
]
