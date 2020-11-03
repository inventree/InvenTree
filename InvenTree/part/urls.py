"""
URL lookup for Part app. Provides URL endpoints for:

- Display / Create / Edit / Delete PartCategory
- Display / Create / Edit / Delete Part
- Create / Edit / Delete PartAttachment
- Display / Create / Edit / Delete SupplierPart

"""

from django.conf.urls import url, include

from . import views

part_related_urls = [
    url(r'^new/?', views.PartRelatedCreate.as_view(), name='part-related-create'),
    url(r'^(?P<pk>\d+)/delete/?', views.PartRelatedDelete.as_view(), name='part-related-delete'),
]

part_attachment_urls = [
    url(r'^new/?', views.PartAttachmentCreate.as_view(), name='part-attachment-create'),
    url(r'^(?P<pk>\d+)/edit/?', views.PartAttachmentEdit.as_view(), name='part-attachment-edit'),
    url(r'^(?P<pk>\d+)/delete/?', views.PartAttachmentDelete.as_view(), name='part-attachment-delete'),
]

sale_price_break_urls = [
    url(r'^new/', views.PartSalePriceBreakCreate.as_view(), name='sale-price-break-create'),
    url(r'^(?P<pk>\d+)/edit/', views.PartSalePriceBreakEdit.as_view(), name='sale-price-break-edit'),
    url(r'^(?P<pk>\d+)/delete/', views.PartSalePriceBreakDelete.as_view(), name='sale-price-break-delete'),
]

part_parameter_urls = [
    
    url(r'^template/new/', views.PartParameterTemplateCreate.as_view(), name='part-param-template-create'),
    url(r'^template/(?P<pk>\d+)/edit/', views.PartParameterTemplateEdit.as_view(), name='part-param-template-edit'),
    url(r'^template/(?P<pk>\d+)/delete/', views.PartParameterTemplateDelete.as_view(), name='part-param-template-edit'),
    
    url(r'^new/', views.PartParameterCreate.as_view(), name='part-param-create'),
    url(r'^(?P<pk>\d+)/edit/', views.PartParameterEdit.as_view(), name='part-param-edit'),
    url(r'^(?P<pk>\d+)/delete/', views.PartParameterDelete.as_view(), name='part-param-delete'),
]

part_detail_urls = [
    url(r'^edit/?', views.PartEdit.as_view(), name='part-edit'),
    url(r'^delete/?', views.PartDelete.as_view(), name='part-delete'),
    url(r'^bom-export/?', views.BomExport.as_view(), name='bom-export'),
    url(r'^bom-download/?', views.BomDownload.as_view(), name='bom-download'),
    url(r'^validate-bom/', views.BomValidate.as_view(), name='bom-validate'),
    url(r'^duplicate/', views.PartDuplicate.as_view(), name='part-duplicate'),
    url(r'^make-variant/', views.MakePartVariant.as_view(), name='make-part-variant'),
    url(r'^pricing/', views.PartPricing.as_view(), name='part-pricing'),
    
    url(r'^bom-upload/?', views.BomUpload.as_view(), name='upload-bom'),
    url(r'^bom-duplicate/?', views.BomDuplicate.as_view(), name='duplicate-bom'),
    
    url(r'^params/', views.PartDetail.as_view(template_name='part/params.html'), name='part-params'),
    url(r'^variants/?', views.PartDetail.as_view(template_name='part/variants.html'), name='part-variants'),
    url(r'^stock/?', views.PartDetail.as_view(template_name='part/stock.html'), name='part-stock'),
    url(r'^allocation/?', views.PartDetail.as_view(template_name='part/allocation.html'), name='part-allocation'),
    url(r'^bom/?', views.PartDetail.as_view(template_name='part/bom.html'), name='part-bom'),
    url(r'^build/?', views.PartDetail.as_view(template_name='part/build.html'), name='part-build'),
    url(r'^used/?', views.PartDetail.as_view(template_name='part/used_in.html'), name='part-used-in'),
    url(r'^suppliers/?', views.PartDetail.as_view(template_name='part/supplier.html'), name='part-suppliers'),
    url(r'^orders/?', views.PartDetail.as_view(template_name='part/orders.html'), name='part-orders'),
    url(r'^sales-orders/', views.PartDetail.as_view(template_name='part/sales_orders.html'), name='part-sales-orders'),
    url(r'^sale-prices/', views.PartDetail.as_view(template_name='part/sale_prices.html'), name='part-sale-prices'),
    url(r'^tests/', views.PartDetail.as_view(template_name='part/part_tests.html'), name='part-test-templates'),
    url(r'^track/?', views.PartDetail.as_view(template_name='part/track.html'), name='part-track'),
    url(r'^related-parts/?', views.PartDetail.as_view(template_name='part/related.html'), name='part-related'),
    url(r'^attachments/?', views.PartDetail.as_view(template_name='part/attachments.html'), name='part-attachments'),
    url(r'^notes/?', views.PartNotes.as_view(), name='part-notes'),
    
    url(r'^qr_code/?', views.PartQRCode.as_view(), name='part-qr'),

    # Normal thumbnail with form
    url(r'^thumbnail/?', views.PartImageUpload.as_view(), name='part-image-upload'),
    url(r'^thumb-select/?', views.PartImageSelect.as_view(), name='part-image-select'),

    # Any other URLs go to the part detail page
    url(r'^.*$', views.PartDetail.as_view(), name='part-detail'),
]

category_parameter_urls = [
    url(r'^new/', views.CategoryParameterTemplateCreate.as_view(), name='category-param-template-create'),
    url(r'^(?P<pid>\d+)/edit/', views.CategoryParameterTemplateEdit.as_view(), name='category-param-template-edit'),
    url(r'^(?P<pid>\d+)/delete/', views.CategoryParameterTemplateDelete.as_view(), name='category-param-template-delete'),
]

part_category_urls = [
    url(r'^edit/?', views.CategoryEdit.as_view(), name='category-edit'),
    url(r'^delete/?', views.CategoryDelete.as_view(), name='category-delete'),

    url(r'^parameters/', include(category_parameter_urls)),

    url(r'^parametric/?', views.CategoryParametric.as_view(), name='category-parametric'),
    url(r'^.*$', views.CategoryDetail.as_view(), name='category-detail'),
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

    # Download a BOM upload template
    url(r'^bom_template/?', views.BomUploadTemplate.as_view(), name='bom-upload-template'),

    # Export data for multiple parts
    url(r'^export/', views.PartExport.as_view(), name='part-export'),

    # Individual part using pk
    url(r'^(?P<pk>\d+)/', include(part_detail_urls)),

    # Part category
    url(r'^category/(?P<pk>\d+)/', include(part_category_urls)),

    # Part related
    url(r'^related-parts/', include(part_related_urls)),

    # Part attachments
    url(r'^attachment/', include(part_attachment_urls)),

    # Part price breaks
    url(r'^sale-price/', include(sale_price_break_urls)),

    # Part test templates
    url(r'^test-template/', include([
        url(r'^new/', views.PartTestTemplateCreate.as_view(), name='part-test-template-create'),
        url(r'^(?P<pk>\d+)/edit/', views.PartTestTemplateEdit.as_view(), name='part-test-template-edit'),
        url(r'^(?P<pk>\d+)/delete/', views.PartTestTemplateDelete.as_view(), name='part-test-template-delete'),
    ])),

    # Part parameters
    url(r'^parameter/', include(part_parameter_urls)),

    # Change category for multiple parts
    url(r'^set-category/?', views.PartSetCategory.as_view(), name='part-set-category'),

    # Bom Items
    url(r'^bom/(?P<pk>\d+)/', include(part_bom_urls)),

    # Individual part using IPN as slug
    url(r'^(?P<slug>[-\w]+)/', views.PartDetailFromIPN.as_view(), name='part-detail-from-ipn'),

    # Top level part list (display top level parts and categories)
    url(r'^.*$', views.PartIndex.as_view(), name='part-index'),
]
