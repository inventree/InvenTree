from django.conf.urls import url, include

from . import views

supplier_part_detail_urls = [
    url(r'edit/?', views.SupplierPartEdit.as_view(), name='supplier-part-edit'),
    url(r'delete/?', views.SupplierPartDelete.as_view(), name='supplier-part-delete'),

    url('^.*$', views.SupplierPartDetail.as_view(), name='supplier-part-detail'),
]

supplier_part_urls = [
    url(r'^new/?', views.SupplierPartCreate.as_view(), name='supplier-part-create'),

    url(r'^(?P<pk>\d+)/', include(supplier_part_detail_urls)),
]

part_detail_urls = [
    url(r'^edit/?', views.PartEdit.as_view(), name='part-edit'),
    url(r'^delete/?', views.PartDelete.as_view(), name='part-delete'),
    url(r'^track/?', views.PartDetail.as_view(template_name='part/track.html'), name='part-track'),
    url(r'^bom/?', views.PartDetail.as_view(template_name='part/bom.html'), name='part-bom'),
    url(r'^export-bom/?', views.BomExport.as_view(), name='bom-export'),
    url(r'^build/?', views.PartDetail.as_view(template_name='part/build.html'), name='part-build'),
    url(r'^stock/?', views.PartDetail.as_view(template_name='part/stock.html'), name='part-stock'),
    url(r'^used/?', views.PartDetail.as_view(template_name='part/used_in.html'), name='part-used-in'),
    url(r'^allocation/?', views.PartDetail.as_view(template_name='part/allocation.html'), name='part-allocation'),
    url(r'^suppliers/?', views.PartDetail.as_view(template_name='part/supplier.html'), name='part-suppliers'),

    url(r'^thumbnail/?', views.PartImage.as_view(), name='part-image'),

    # Any other URLs go to the part detail page
    url(r'^.*$', views.PartDetail.as_view(), name='part-detail'),
]

part_category_urls = [
    url(r'^edit/?', views.CategoryEdit.as_view(), name='category-edit'),
    url(r'^delete/?', views.CategoryDelete.as_view(), name='category-delete'),

    url('^.*$', views.CategoryDetail.as_view(), name='category-detail'),
]

part_bom_urls = [
    url(r'^edit/?', views.BomItemEdit.as_view(), name='bom-item-edit'),
    url('^delete/?', views.BomItemDelete.as_view(), name='bom-item-delete'),

    url(r'^.*$', views.BomItemDetail.as_view(), name='bom-item-detail'),
]

# URL list for part web interface
part_urls = [

    # Create a new category
    url(r'^category/new/?', views.CategoryCreate.as_view(), name='category-create'),

    # Create a new part
    url(r'^new/?', views.PartCreate.as_view(), name='part-create'),

    # Create a new BOM item
    url(r'^bom/new/?', views.BomItemCreate.as_view(), name='bom-item-create'),

    # Individual part
    url(r'^(?P<pk>\d+)/', include(part_detail_urls)),

    # Part category
    url(r'^category/(?P<pk>\d+)/', include(part_category_urls)),

    url(r'^bom/(?P<pk>\d+)/', include(part_bom_urls)),

    # Top level part list (display top level parts and categories)
    url(r'^.*$', views.PartIndex.as_view(), name='part-index'),
]

"""
part_param_urls = [
    # Detail of a single part parameter
    url(r'^(?P<pk>[0-9]+)/?$', views.PartParamDetail.as_view(), name='partparameter-detail'),

    # Parameters associated with a particular part
    url(r'^\?.*/?$', views.PartParamList.as_view()),
    url(r'^$', views.PartParamList.as_view()),
]

part_param_template_urls = [
    # Detail of a single part field template
    url(r'^(?P<pk>[0-9]+)/?$', views.PartTemplateDetail.as_view(), name='partparametertemplate-detail'),

    # List all part field templates
    url(r'^\?.*/?$', views.PartTemplateList.as_view()),
    url(r'^$', views.PartTemplateList.as_view())
]
"""
