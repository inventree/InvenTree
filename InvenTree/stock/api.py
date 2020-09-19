"""
JSON API for the Stock app
"""

from django_filters.rest_framework import FilterSet, DjangoFilterBackend
from django_filters import NumberFilter

from rest_framework import status

from django.conf.urls import url, include
from django.urls import reverse
from django.http import JsonResponse
from django.db.models import Q

from .models import StockLocation, StockItem
from .models import StockItemTracking
from .models import StockItemAttachment
from .models import StockItemTestResult

from part.models import Part, PartCategory
from part.serializers import PartBriefSerializer

from company.models import SupplierPart
from company.serializers import SupplierPartSerializer

from .serializers import StockItemSerializer
from .serializers import LocationSerializer, LocationBriefSerializer
from .serializers import StockTrackingSerializer
from .serializers import StockItemAttachmentSerializer
from .serializers import StockItemTestResultSerializer

from InvenTree.views import TreeSerializer
from InvenTree.helpers import str2bool, isNull
from InvenTree.api import AttachmentMixin

from decimal import Decimal, InvalidOperation

from rest_framework.serializers import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, filters, permissions


class StockCategoryTree(TreeSerializer):
    title = 'Stock'
    model = StockLocation

    @property
    def root_url(self):
        return reverse('stock-index')

    def get_items(self):
        return StockLocation.objects.all().prefetch_related('stock_items', 'children')


class StockDetail(generics.RetrieveUpdateDestroyAPIView):
    """ API detail endpoint for Stock object

    get:
    Return a single StockItem object

    post:
    Update a StockItem

    delete:
    Remove a StockItem
    """

    queryset = StockItem.objects.all()
    serializer_class = StockItemSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self, *args, **kwargs):

        queryset = super().get_queryset(*args, **kwargs)
        queryset = StockItemSerializer.prefetch_queryset(queryset)
        queryset = StockItemSerializer.annotate_queryset(queryset)

        return queryset

    def get_serializer(self, *args, **kwargs):

        kwargs['part_detail'] = True
        kwargs['location_detail'] = True
        kwargs['supplier_part_detail'] = True
        kwargs['test_detail'] = True
        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)


class StockFilter(FilterSet):
    """ FilterSet for advanced stock filtering.

    Allows greater-than / less-than filtering for stock quantity
    """

    min_stock = NumberFilter(name='quantity', lookup_expr='gte')
    max_stock = NumberFilter(name='quantity', lookup_expr='lte')

    class Meta:
        model = StockItem
        fields = ['quantity', 'part', 'location']


class StockAdjust(APIView):
    """
    A generic class for handling stocktake actions.

    Subclasses exist for:
    
    - StockCount: count stock items
    - StockAdd: add stock items
    - StockRemove: remove stock items
    - StockTransfer: transfer stock items
    """

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get_items(self, request):
        """
        Return a list of items posted to the endpoint.
        Will raise validation errors if the items are not
        correctly formatted.
        """

        _items = []

        if 'item' in request.data:
            _items = [request.data['item']]
        elif 'items' in request.data:
            _items = request.data['items']
        else:
            raise ValidationError({'items': 'Request must contain list of stock items'})

        # List of validated items
        self.items = []

        for entry in _items:

            if not type(entry) == dict:
                raise ValidationError({'error': 'Improperly formatted data'})

            try:
                pk = entry.get('pk', None)
                item = StockItem.objects.get(pk=pk)
            except (ValueError, StockItem.DoesNotExist):
                raise ValidationError({'pk': 'Each entry must contain a valid pk field'})

            try:
                quantity = Decimal(str(entry.get('quantity', None)))
            except (ValueError, TypeError, InvalidOperation):
                raise ValidationError({'quantity': 'Each entry must contain a valid quantity field'})

            if quantity < 0:
                raise ValidationError({'quantity': 'Quantity field must not be less than zero'})

            self.items.append({
                'item': item,
                'quantity': quantity
            })

        self.notes = str(request.data.get('notes', ''))


class StockCount(StockAdjust):
    """
    Endpoint for counting stock (performing a stocktake).
    """
    
    def post(self, request, *args, **kwargs):

        self.get_items(request)

        n = 0

        for item in self.items:

            if item['item'].stocktake(item['quantity'], request.user, notes=self.notes):
                n += 1

        return Response({'success': 'Updated stock for {n} items'.format(n=n)})


class StockAdd(StockAdjust):
    """
    Endpoint for adding a quantity of stock to an existing StockItem
    """

    def post(self, request, *args, **kwargs):

        self.get_items(request)

        n = 0

        for item in self.items:
            if item['item'].add_stock(item['quantity'], request.user, notes=self.notes):
                n += 1

        return Response({"success": "Added stock for {n} items".format(n=n)})


class StockRemove(StockAdjust):
    """
    Endpoint for removing a quantity of stock from an existing StockItem.
    """

    def post(self, request, *args, **kwargs):

        self.get_items(request)
        
        n = 0

        for item in self.items:

            if item['item'].take_stock(item['quantity'], request.user, notes=self.notes):
                n += 1

        return Response({"success": "Removed stock for {n} items".format(n=n)})


class StockTransfer(StockAdjust):
    """
    API endpoint for performing stock movements
    """

    def post(self, request, *args, **kwargs):

        self.get_items(request)

        data = request.data

        try:
            location = StockLocation.objects.get(pk=data.get('location', None))
        except (ValueError, StockLocation.DoesNotExist):
            raise ValidationError({'location': 'Valid location must be specified'})

        n = 0

        for item in self.items:

            # If quantity is not specified, move the entire stock
            if item['quantity'] in [0, None]:
                item['quantity'] = item['item'].quantity

            if item['item'].move(location, self.notes, request.user, quantity=item['quantity']):
                n += 1

        return Response({'success': 'Moved {n} parts to {loc}'.format(
            n=n,
            loc=str(location),
        )})


class StockLocationList(generics.ListCreateAPIView):
    """ API endpoint for list view of StockLocation objects:

    - GET: Return list of StockLocation objects
    - POST: Create a new StockLocation
    """

    queryset = StockLocation.objects.all()
    serializer_class = LocationSerializer

    def get_queryset(self):
        """
        Custom filtering:
        - Allow filtering by "null" parent to retrieve top-level stock locations
        """

        queryset = super().get_queryset()

        loc_id = self.request.query_params.get('parent', None)

        if loc_id is not None:

            # Look for top-level locations
            if isNull(loc_id):
                queryset = queryset.filter(parent=None)
            
            else:
                try:
                    loc_id = int(loc_id)
                    queryset = queryset.filter(parent=loc_id)
                except ValueError:
                    pass
            
        return queryset

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filter_fields = [
    ]

    search_fields = [
        'name',
        'description',
    ]


class StockList(generics.ListCreateAPIView):
    """ API endpoint for list view of Stock objects

    - GET: Return a list of all StockItem objects (with optional query filters)
    - POST: Create a new StockItem

    Additional query parameters are available:
        - location: Filter stock by location
        - category: Filter by parts belonging to a certain category
        - supplier: Filter by supplier
        - ancestor: Filter by an 'ancestor' StockItem
        - status: Filter by the StockItem status
    """

    serializer_class = StockItemSerializer
    queryset = StockItem.objects.all()

    # TODO - Override the 'create' method for this view,
    # to allow the user to be recorded when a new StockItem object is created

    def list(self, request, *args, **kwargs):
        """
        Override the 'list' method, as the StockLocation objects
        are very expensive to serialize.
        
        So, we fetch and serialize the required StockLocation objects only as required.
        """

        queryset = self.filter_queryset(self.get_queryset())

        serializer = self.get_serializer(queryset, many=True)

        data = serializer.data

        # Keep track of which related models we need to query
        location_ids = set()
        part_ids = set()
        supplier_part_ids = set()

        # Iterate through each StockItem and grab some data
        for item in data:
            loc = item['location']
            if loc:
                location_ids.add(loc)

            part = item['part']
            if part:
                part_ids.add(part)

            sp = item['supplier_part']

            if sp:
                supplier_part_ids.add(sp)

        # Do we wish to include Part detail?
        if str2bool(request.query_params.get('part_detail', False)):

            # Fetch only the required Part objects from the database
            parts = Part.objects.filter(pk__in=part_ids).prefetch_related(
                'category',
            )

            part_map = {}

            for part in parts:
                part_map[part.pk] = PartBriefSerializer(part).data

            # Now update each StockItem with the related Part data
            for stock_item in data:
                part_id = stock_item['part']
                stock_item['part_detail'] = part_map.get(part_id, None)

        # Do we wish to include SupplierPart detail?
        if str2bool(request.query_params.get('supplier_part_detail', False)):

            supplier_parts = SupplierPart.objects.filter(pk__in=supplier_part_ids)

            supplier_part_map = {}

            for part in supplier_parts:
                supplier_part_map[part.pk] = SupplierPartSerializer(part).data

            for stock_item in data:
                part_id = stock_item['supplier_part']
                stock_item['supplier_part_detail'] = supplier_part_map.get(part_id, None)

        # Do we wish to include StockLocation detail?
        if str2bool(request.query_params.get('location_detail', False)):

            # Fetch only the required StockLocation objects from the database
            locations = StockLocation.objects.filter(pk__in=location_ids).prefetch_related(
                'parent',
                'children',
            )

            location_map = {}

            # Serialize each StockLocation object
            for location in locations:
                location_map[location.pk] = LocationBriefSerializer(location).data

            # Now update each StockItem with the related StockLocation data
            for stock_item in data:
                loc_id = stock_item['location']
                stock_item['location_detail'] = location_map.get(loc_id, None)

        """
        Determine the response type based on the request.
        a) For HTTP requests (e.g. via the browseable API) return a DRF response
        b) For AJAX requests, simply return a JSON rendered response.

        Note: b) is about 100x quicker than a), because the DRF framework adds a lot of cruft
        """

        if request.is_ajax():
            return JsonResponse(data, safe=False)
        else:
            return Response(data)

    def get_queryset(self, *args, **kwargs):

        queryset = super().get_queryset(*args, **kwargs)

        queryset = StockItemSerializer.prefetch_queryset(queryset)
        queryset = StockItemSerializer.annotate_queryset(queryset)

        return queryset

    def filter_queryset(self, queryset):

        params = self.request.query_params

        queryset = super().filter_queryset(queryset)

        # Perform basic filtering:
        # Note: We do not let DRF filter here, it be slow AF

        supplier_part = params.get('supplier_part', None)

        if supplier_part:
            queryset = queryset.filter(supplier_part=supplier_part)

        belongs_to = params.get('belongs_to', None)

        if belongs_to:
            queryset = queryset.filter(belongs_to=belongs_to)

        build = params.get('build', None)

        if build:
            queryset = queryset.filter(build=build)

        build_order = params.get('build_order', None)

        if build_order:
            queryset = queryset.filter(build_order=build_order)

        sales_order = params.get('sales_order', None)

        if sales_order:
            queryset = queryset.filter(sales_order=sales_order)

        # Filter by customer
        customer = params.get('customer', None)

        if customer:
            queryset = queryset.filter(customer=customer)

        # Filter if items have been sent to a customer (any customer)
        sent_to_customer = params.get('sent_to_customer', None)

        if sent_to_customer is not None:
            sent_to_customer = str2bool(sent_to_customer)

            if sent_to_customer:
                queryset = queryset.exclude(customer=None)
            else:
                queryset = queryset.filter(customer=None)

        # Filter by "serialized" status?
        serialized = params.get('serialized', None)

        if serialized is not None:
            serialized = str2bool(serialized)

            if serialized:
                queryset = queryset.exclude(serial=None)
            else:
                queryset = queryset.filter(serial=None)

        # Filter by serial number?
        serial_number = params.get('serial', None)

        if serial_number is not None:
            queryset = queryset.filter(serial=serial_number)

        # Filter by range of serial numbers?
        serial_number_gte = params.get('serial_gte', None)
        serial_number_lte = params.get('serial_lte', None)

        if serial_number_gte is not None or serial_number_lte is not None:
            queryset = queryset.exclude(serial=None)

        if serial_number_gte is not None:
            queryset = queryset.filter(serial__gte=serial_number_gte)
        
        if serial_number_lte is not None:
            queryset = queryset.filter(serial__lte=serial_number_lte)

        # Filter by "in_stock" status
        in_stock = params.get('in_stock', None)

        if in_stock is not None:
            in_stock = str2bool(in_stock)

            if in_stock:
                # Filter out parts which are not actually "in stock"
                queryset = queryset.filter(StockItem.IN_STOCK_FILTER)
            else:
                # Only show parts which are not in stock
                queryset = queryset.exclude(StockItem.IN_STOCK_FILTER)

        # Filter by 'allocated' patrs?
        allocated = params.get('allocated', None)

        if allocated is not None:
            allocated = str2bool(allocated)

            if allocated:
                # Filter StockItem with either build allocations or sales order allocations
                queryset = queryset.filter(Q(sales_order_allocations__isnull=False) | Q(allocations__isnull=False))
            else:
                # Filter StockItem without build allocations or sales order allocations
                queryset = queryset.filter(Q(sales_order_allocations__isnull=True) & Q(allocations__isnull=True))
                
        # Do we wish to filter by "active parts"
        active = self.request.query_params.get('active', None)

        if active is not None:
            active = str2bool(active)
            queryset = queryset.filter(part__active=active)

        # Filter by 'depleted' status
        depleted = params.get('depleted', None)

        if depleted is not None:
            depleted = str2bool(depleted)

            if depleted:
                queryset = queryset.filter(quantity__lte=0)
            else:
                queryset = queryset.exclude(quantity__lte=0)

        # Filter by internal part number
        IPN = params.get('IPN', None)

        if IPN is not None:
            queryset = queryset.filter(part__IPN=IPN)

        # Does the client wish to filter by the Part ID?
        part_id = params.get('part', None)

        if part_id:
            try:
                part = Part.objects.get(pk=part_id)

                # Filter by any parts "under" the given part
                parts = part.get_descendants(include_self=True)

                queryset = queryset.filter(part__in=parts)

            except (ValueError, Part.DoesNotExist):
                raise ValidationError({"part": "Invalid Part ID specified"})

        # Does the client wish to filter by the 'ancestor'?
        anc_id = self.request.query_params.get('ancestor', None)

        if anc_id:
            try:
                ancestor = StockItem.objects.get(pk=anc_id)

                # Only allow items which are descendants of the specified StockItem
                queryset = queryset.filter(id__in=[item.pk for item in ancestor.children.all()])

            except (ValueError, Part.DoesNotExist):
                raise ValidationError({"ancestor": "Invalid ancestor ID specified"})

        # Does the client wish to filter by stock location?
        loc_id = self.request.query_params.get('location', None)

        cascade = str2bool(self.request.query_params.get('cascade', True))

        if loc_id is not None:

            # Filter by 'null' location (i.e. top-level items)
            if isNull(loc_id):
                queryset = queryset.filter(location=None)
            else:
                try:
                    # If '?cascade=true' then include items which exist in sub-locations
                    if cascade:
                        location = StockLocation.objects.get(pk=loc_id)
                        queryset = queryset.filter(location__in=location.getUniqueChildren())
                    else:
                        queryset = queryset.filter(location=loc_id)
                    
                except (ValueError, StockLocation.DoesNotExist):
                    pass

        # Does the client wish to filter by part category?
        cat_id = self.request.query_params.get('category', None)

        if cat_id:
            try:
                category = PartCategory.objects.get(pk=cat_id)
                queryset = queryset.filter(part__category__in=category.getUniqueChildren())

            except (ValueError, PartCategory.DoesNotExist):
                raise ValidationError({"category": "Invalid category id specified"})

        # Filter by StockItem status
        status = self.request.query_params.get('status', None)

        if status:
            queryset = queryset.filter(status=status)

        # Filter by supplier_part ID
        supplier_part_id = self.request.query_params.get('supplier_part', None)

        if supplier_part_id:
            queryset = queryset.filter(supplier_part=supplier_part_id)

        # Filter by company (either manufacturer or supplier)
        company = self.request.query_params.get('company', None)

        if company is not None:
            queryset = queryset.filter(Q(supplier_part__supplier=company) | Q(supplier_part__manufacturer=company))

        # Filter by supplier
        supplier = self.request.query_params.get('supplier', None)

        if supplier is not None:
            queryset = queryset.filter(supplier_part__supplier=supplier)

        # Filter by manufacturer
        manufacturer = self.request.query_params.get('manufacturer', None)

        if manufacturer is not None:
            queryset = queryset.filter(supplier_part__manufacturer=manufacturer)

        # Also ensure that we pre-fecth all the related items
        queryset = queryset.prefetch_related(
            'part',
            'part__category',
            'location'
        )

        queryset = queryset.order_by('part__name')

        return queryset

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filter_fields = [
    ]

    search_fields = [
        'serial',
        'batch',
        'part__name',
        'part__IPN',
        'part__description'
    ]


class StockAttachmentList(generics.ListCreateAPIView, AttachmentMixin):
    """
    API endpoint for listing (and creating) a StockItemAttachment (file upload)
    """

    queryset = StockItemAttachment.objects.all()
    serializer_class = StockItemAttachmentSerializer

    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]

    filter_fields = [
        'stock_item',
    ]


class StockItemTestResultList(generics.ListCreateAPIView):
    """
    API endpoint for listing (and creating) a StockItemTestResult object.
    """

    queryset = StockItemTestResult.objects.all()
    serializer_class = StockItemTestResultSerializer

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filter_fields = [
        'stock_item',
        'test',
        'user',
        'result',
        'value',
    ]

    ordering = 'date'

    def get_serializer(self, *args, **kwargs):
        try:
            kwargs['user_detail'] = str2bool(self.request.query_params.get('user_detail', False))
        except:
            pass

        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

    def perform_create(self, serializer):
        """
        Create a new test result object.

        Also, check if an attachment was uploaded alongside the test result,
        and save it to the database if it were.
        """

        # Capture the user information
        test_result = serializer.save()
        test_result.user = self.request.user
        test_result.save()


class StockTrackingList(generics.ListCreateAPIView):
    """ API endpoint for list view of StockItemTracking objects.

    StockItemTracking objects are read-only
    (they are created by internal model functionality)

    - GET: Return list of StockItemTracking objects
    """

    queryset = StockItemTracking.objects.all()
    serializer_class = StockTrackingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer(self, *args, **kwargs):
        try:
            kwargs['item_detail'] = str2bool(self.request.query_params.get('item_detail', False))
        except:
            pass

        try:
            kwargs['user_detail'] = str2bool(self.request.query_params.get('user_detail', False))
        except:
            pass

        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        """ Create a new StockItemTracking object
        
        Here we override the default 'create' implementation,
        to save the user information associated with the request object.
        """

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Record the user who created this Part object
        item = serializer.save()
        item.user = request.user
        item.system = False

        # quantity field cannot be explicitly adjusted  here
        item.quantity = item.item.quantity
        item.save()

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filter_fields = [
        'item',
        'user',
    ]

    ordering = '-date'

    ordering_fields = [
        'date',
    ]

    search_fields = [
        'title',
        'notes',
    ]


class LocationDetail(generics.RetrieveUpdateDestroyAPIView):
    """ API endpoint for detail view of StockLocation object

    - GET: Return a single StockLocation object
    - PATCH: Update a StockLocation object
    - DELETE: Remove a StockLocation object
    """

    queryset = StockLocation.objects.all()
    serializer_class = LocationSerializer
    permission_classes = (permissions.IsAuthenticated,)


stock_endpoints = [
    url(r'^$', StockDetail.as_view(), name='api-stock-detail'),
]

location_endpoints = [
    url(r'^(?P<pk>\d+)/', LocationDetail.as_view(), name='api-location-detail'),

    url(r'^.*$', StockLocationList.as_view(), name='api-location-list'),
]

stock_api_urls = [
    url(r'location/', include(location_endpoints)),

    # These JSON endpoints have been replaced (for now) with server-side form rendering - 02/06/2019
    url(r'count/?', StockCount.as_view(), name='api-stock-count'),
    url(r'add/?', StockAdd.as_view(), name='api-stock-add'),
    url(r'remove/?', StockRemove.as_view(), name='api-stock-remove'),
    url(r'transfer/?', StockTransfer.as_view(), name='api-stock-transfer'),

    # Base URL for StockItemAttachment API endpoints
    url(r'^attachment/', include([
        url(r'^$', StockAttachmentList.as_view(), name='api-stock-attachment-list'),
    ])),

    # Base URL for StockItemTestResult API endpoints
    url(r'^test/', include([
        url(r'^$', StockItemTestResultList.as_view(), name='api-stock-test-result-list'),
    ])),

    url(r'track/?', StockTrackingList.as_view(), name='api-stock-track'),

    url(r'^tree/?', StockCategoryTree.as_view(), name='api-stock-tree'),

    # Detail for a single stock item
    url(r'^(?P<pk>\d+)/', include(stock_endpoints)),

    url(r'^.*$', StockList.as_view(), name='api-stock-list'),
]
