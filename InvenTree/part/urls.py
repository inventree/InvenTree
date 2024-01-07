"""URL lookup for Part app. Provides URL endpoints for:

- Display / Create / Edit / Delete PartCategory
- Display / Create / Edit / Delete Part
- Create / Edit / Delete PartAttachment
- Display / Create / Edit / Delete SupplierPart
"""

from django.urls import include, path, re_path

from . import views

part_detail_urls = [
    re_path(r'^bom-upload/?', views.BomUpload.as_view(), name='upload-bom'),
    # Normal thumbnail with form
    re_path(
        r'^thumb-select/?', views.PartImageSelect.as_view(), name='part-image-select'
    ),
    # Any other URLs go to the part detail page
    re_path(r'^.*$', views.PartDetail.as_view(), name='part-detail'),
]

category_urls = [
    # Category detail views
    re_path(r'(?P<pk>\d+)/', views.CategoryDetail.as_view(), name='category-detail')
]

# URL list for part web interface
part_urls = [
    # Upload a part
    re_path(r'^import/$', views.PartImport.as_view(), name='part-import'),
    re_path(
        r'^import/?', views.PartImportTemplate.as_view(), name='part-template-download'
    ),
    re_path(r'^import-api/', views.PartImportAjax.as_view(), name='api-part-import'),
    # Individual part using pk
    path(r'<int:pk>/', include(part_detail_urls)),
    # Part category
    re_path(r'^category/', include(category_urls)),
    # Individual part using IPN as slug
    re_path(
        r'^(?P<slug>[-\w]+)/',
        views.PartDetailFromIPN.as_view(),
        name='part-detail-from-ipn',
    ),
    # Top level part list (display top level parts and categories)
    re_path(r'^.*$', views.PartIndex.as_view(), name='part-index'),
]
