"""URL lookup for Company app."""

from django.urls import include, path

from . import views

company_urls = [
    # Detail URLs for a specific Company instance
    path(
        '<int:pk>/',
        include([path('', views.CompanyDetail.as_view(), name='company-detail')]),
    ),
    path('suppliers/', views.CompanyIndex.as_view(), name='supplier-index'),
    path('manufacturers/', views.CompanyIndex.as_view(), name='manufacturer-index'),
    path('customers/', views.CompanyIndex.as_view(), name='customer-index'),
    # Redirect any other patterns to the 'company' index which displays all companies
    path('', views.CompanyIndex.as_view(), name='company-index'),
]

manufacturer_part_urls = [
    path(
        '<int:pk>/',
        views.ManufacturerPartDetail.as_view(
            template_name='company/manufacturer_part.html'
        ),
        name='manufacturer-part-detail',
    )
]

supplier_part_urls = [
    path(
        '<int:pk>/',
        include([
            path(
                '',
                views.SupplierPartDetail.as_view(
                    template_name='company/supplier_part.html'
                ),
                name='supplier-part-detail',
            )
        ]),
    )
]
