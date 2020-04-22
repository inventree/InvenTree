"""
JSON API for the Stock app
"""

from django_filters.rest_framework import FilterSet, DjangoFilterBackend
from django_filters import NumberFilter

from django.conf.urls import url, include
from django.urls import reverse
from django.db.models import Q

from .models import StockLocation, StockItem
from .models import StockItemTracking

from part.models import Part, PartCategory

from .serializers import StockItemSerializer
from .serializers import LocationSerializer
from .serializers import StockTrackingSerializer

from InvenTree.views import TreeSerializer
from InvenTree.helpers import str2bool, isNull

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

        try:
            kwargs['part_detail'] = str2bool(self.request.query_params.get('part_detail', False))
        except AttributeError:
            pass

        try:
            kwargs['location_detail'] = str2bool(self.request.query_params.get('location_detail', False))
        except AttributeError:
            pass

        try:
            kwargs['supplier_part_detail'] = str2bool(self.request.query_params.get('supplier_detail', False))
        except AttributeError:
            pass

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
    Endpoint for adding stock
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
    Endpoint for removing stock.
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
        - aggregate: If 'true' then stock items are aggregated by Part and Location
        - location: Filter stock by location
        - category: Filter by parts belonging to a certain category
        - supplier: Filter by supplier
        - ancestor: Filter by an 'ancestor' StockItem
        - status: Filter by the StockItem status
    """

    serializer_class = StockItemSerializer

    queryset = StockItem.objects.all()

    def get_serializer(self, *args, **kwargs):

        try:
            kwargs['part_detail'] = str2bool(self.request.query_params.get('part_detail', None))
        except AttributeError:
            pass

        try:
            kwargs['location_detail'] = str2bool(self.request.query_params.get('location_detail', None))
        except AttributeError:
            pass

        try:
            kwargs['supplier_part_detail'] = str2bool(self.request.query_params.get('supplier_part_detail', None))
        except AttributeError:
            pass
        
        # Ensure the request context is passed through
        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

    # TODO - Override the 'create' method for this view,
    # to allow the user to be recorded when a new StockItem object is created

    def get_queryset(self, *args, **kwargs):

        queryset = super().get_queryset(*args, **kwargs)
        queryset = StockItemSerializer.prefetch_queryset(queryset)

        return queryset

    def filter_queryset(self, queryset):

        # Start with all objects
        stock_list = super().filter_queryset(queryset)
        
        # Filter out parts which are not actually "in stock"
        stock_list = stock_list.filter(customer=None, belongs_to=None)

        # Filter by 'allocated' patrs?
        allocated = self.request.query_params.get('allocated', None)

        if allocated is not None:
            allocated = str2bool(allocated)

            if allocated:
                # Filter StockItem with either build allocations or sales order allocations
                stock_list = stock_list.filter(Q(sales_order_allocations__isnull=False) | Q(allocations__isnull=False))
            else:
                # Filter StockItem without build allocations or sales order allocations
                stock_list = stock_list.filter(Q(sales_order_allocations__isnull=True) & Q(allocations__isnull=True))
                
        # Do we wish to filter by "active parts"
        active = self.request.query_params.get('active', None)

        if active is not None:
            active = str2bool(active)
            stock_list = stock_list.filter(part__active=active)

        # Does the client wish to filter by the Part ID?
        part_id = self.request.query_params.get('part', None)

        if part_id:
            try:
                part = Part.objects.get(pk=part_id)

                # If the part is a Template part, select stock items for any "variant" parts under that template
                if part.is_template:
                    stock_list = stock_list.filter(part__in=[part.id for part in Part.objects.filter(variant_of=part_id)])
                else:
                    stock_list = stock_list.filter(part=part_id)

            except (ValueError, Part.DoesNotExist):
                raise ValidationError({"part": "Invalid Part ID specified"})

        # Does the client wish to filter by the 'ancestor'?
        anc_id = self.request.query_params.get('ancestor', None)

        if anc_id:
            try:
                ancestor = StockItem.objects.get(pk=anc_id)

                # Only allow items which are descendants of the specified StockItem
                stock_list = stock_list.filter(id__in=[item.pk for item in ancestor.children.all()])

            except (ValueError, Part.DoesNotExist):
                raise ValidationError({"ancestor": "Invalid ancestor ID specified"})

        # Does the client wish to filter by stock location?
        loc_id = self.request.query_params.get('location', None)

        cascade = str2bool(self.request.query_params.get('cascade', False))

        if loc_id is not None:

            # Filter by 'null' location (i.e. top-level items)
            if isNull(loc_id):
                stock_list = stock_list.filter(location=None)
            else:
                try:
                    # If '?cascade=true' then include items which exist in sub-locations
                    if cascade:
                        location = StockLocation.objects.get(pk=loc_id)
                        stock_list = stock_list.filter(location__in=location.getUniqueChildren())
                    else:
                        stock_list = stock_list.filter(location=loc_id)
                    
                except (ValueError, StockLocation.DoesNotExist):
                    pass

        # Does the client wish to filter by part category?
        cat_id = self.request.query_params.get('category', None)

        if cat_id:
            try:
                category = PartCategory.objects.get(pk=cat_id)
                stock_list = stock_list.filter(part__category__in=category.getUniqueChildren())

            except (ValueError, PartCategory.DoesNotExist):
                raise ValidationError({"category": "Invalid category id specified"})

        # Filter by StockItem status
        status = self.request.query_params.get('status', None)

        if status:
            stock_list = stock_list.filter(status=status)

        # Filter by supplier_part ID
        supplier_part_id = self.request.query_params.get('supplier_part', None)

        if supplier_part_id:
            stock_list = stock_list.filter(supplier_part=supplier_part_id)

        # Filter by company (either manufacturer or supplier)
        company = self.request.query_params.get('company', None)

        if company is not None:
            stock_list = stock_list.filter(Q(supplier_part__supplier=company) | Q(supplier_part__manufacturer=company))

        # Filter by supplier
        supplier = self.request.query_params.get('supplier', None)

        if supplier is not None:
            stock_list = stock_list.filter(supplier_part__supplier=supplier)

        # Filter by manufacturer
        manufacturer = self.request.query_params.get('manufacturer', None)

        if manufacturer is not None:
            stock_list = stock_list.filter(supplier_part__manufacturer=manufacturer)

        # Also ensure that we pre-fecth all the related items
        stock_list = stock_list.prefetch_related(
            'part',
            'part__category',
            'location'
        )

        stock_list = stock_list.order_by('part__name')

        return stock_list

    serializer_class = StockItemSerializer

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filter_fields = [
        'supplier_part',
        'customer',
        'belongs_to',
        'build',
        'sales_order',
    ]


class StockTrackingList(generics.ListCreateAPIView):
    """ API endpoint for list view of StockItemTracking objects.

    StockItemTracking objects are read-only
    (they are created by internal model functionality)

    - GET: Return list of StockItemTracking objects
    """

    queryset = StockItemTracking.objects.all()
    serializer_class = StockTrackingSerializer
    permission_classes = [permissions.IsAuthenticated]

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

    url(r'track/?', StockTrackingList.as_view(), name='api-stock-track'),

    url(r'^tree/?', StockCategoryTree.as_view(), name='api-stock-tree'),

    # Detail for a single stock item
    url(r'^(?P<pk>\d+)/', include(stock_endpoints)),

    url(r'^.*$', StockList.as_view(), name='api-stock-list'),
]
