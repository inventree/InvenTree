# inven_tree_custom/dispatch/urls.py
from django.urls import path
from . import views

# Application namespace for this plugin's dispatch app
# This is not strictly required here but good practice if including these URLs
# via an app_name in the main plugin's get_urls method or if this app were standalone.
# For now, the namespacing will primarily come from the include() in the main plugin.py
# app_name = 'inventreecustom_dispatch' 

urlpatterns = [
    path('', views.DispatchListView.as_view(), name='dispatch_list'),
    path('create/', views.DispatchCreateView.as_view(), name='dispatch_create'),
    path('<int:pk>/', views.DispatchDetailView.as_view(), name='dispatch_detail'),
    path('<int:pk>/update/', views.DispatchUpdateView.as_view(), name='dispatch_update'),
    
    # Placeholder for the URL to add an item to a dispatch.
    # This will be connected to the add_item_to_dispatch view function/method later.
    # Example:
    path('<int:dispatch_pk>/add_item/', views.add_item_to_dispatch, name='dispatch_add_item'),
]
