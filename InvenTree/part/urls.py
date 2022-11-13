"""URL lookup for Part app. Provides URL endpoints for:

- Display / Create / Edit / Delete PartCategory
- Display / Create / Edit / Delete Part
- Create / Edit / Delete PartAttachment
- Display / Create / Edit / Delete SupplierPart
"""

from django.urls import include, re_path

from . import views

part_detail_urls = [
    re_path(r'^bom-download/?', views.BomDownload.as_view(), name='bom-download'),
    re_path(r'^bom-upload/?', views.BomUpload.as_view(), name='upload-bom'),
    re_path(r'^qr_code/?', views.PartQRCode.as_view(), name='part-qr'),
]

# URL list for part web interface
part_urls = [

    # Upload a part
    re_path(r'^import/', views.PartImport.as_view(), name='part-import'),
    re_path(r'^import-api/', views.PartImportAjax.as_view(), name='api-part-import'),

    # Download a BOM upload template
    re_path(r'^bom_template/?', views.BomUploadTemplate.as_view(), name='bom-upload-template'),

    # Individual part using pk
    re_path(r'^(?P<pk>\d+)/', include(part_detail_urls)),
]
