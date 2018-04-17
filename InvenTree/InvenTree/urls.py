from django.conf.urls import url, include
from django.contrib import admin

from part.urls import part_api_urls, part_cat_api_urls
from part.urls import bom_api_urls
from part.urls import part_urls

from stock.urls import stock_api_urls, stock_api_loc_urls
from stock.urls import stock_urls

# from supplier.urls import supplier_api_urls, supplier_api_part_urls
from supplier.urls import supplier_urls

from build.urls import build_urls

from customer_orders.urls import customer_orders_urls

from django.conf import settings
from django.conf.urls.static import static

from django.views.generic.base import RedirectView

# from project.urls import prj_urls, prj_part_urls, prj_cat_urls, prj_run_urls
# from track.urls import unique_urls, part_track_urls

from users.urls import user_urls

admin.site.site_header = "InvenTree Admin"

apipatterns = [

    # Stock URLs
    url(r'^stock/', include(stock_api_urls)),
    url(r'^stock-location/', include(stock_api_loc_urls)),

    # Part URLs
    url(r'^part/', include(part_api_urls)),
    url(r'^part-category/', include(part_cat_api_urls)),
    # url(r'^part-param/', include(part_param_urls)),
    # url(r'^part-param-template/', include(part_param_template_urls)),

    # Part BOM URLs
    url(r'^bom/', include(bom_api_urls)),

    # Supplier URLs
    # url(r'^supplier/', include(supplier_api_urls)),
    # url(r'^supplier-part/', include(supplier_api_part_urls)),
    # url(r'^price-break/', include(price_break_urls)),
    # url(r'^manufacturer/', include(manu_urls)),
    # url(r'^customer/', include(cust_urls)),

    # Tracking URLs
    # url(r'^track/', include(part_track_urls)),
    # url(r'^unique-part/', include(unique_urls)),

    # Project URLs
    # url(r'^project/', include(prj_urls)),
    # url(r'^project-category/', include(prj_cat_urls)),
    # url(r'^project-part/', include(prj_part_urls)),
    # url(r'^project-run/', include(prj_run_urls)),

    # User URLs
    url(r'^user/', include(user_urls)),
]

urlpatterns = [

    # API URL
    # url(r'^api/', include(apipatterns)),
    # url(r'^api-doc/', include_docs_urls(title='InvenTree API')),

    url(r'^part/', include(part_urls)),
    url(r'^stock/', include(stock_urls)),
    url(r'^supplier/', include(supplier_urls)),
    url(r'^build/', include(build_urls)),
    url(r'^customer-orders/', include(customer_orders_urls)),

    url(r'^admin/', admin.site.urls),
    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),
]

# Static file access
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    # Media file access
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Send any unknown URLs to the parts page
urlpatterns += [url(r'^.*$', RedirectView.as_view(url='/part/', permanent=False), name='part-index')]
