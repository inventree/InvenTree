from django_filters.rest_framework import FilterSet, DjangoFilterBackend
from django_filters import NumberFilter

from django.conf.urls import url, include
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import StockLocation, StockItem
from .models import StockItemTracking

from .serializers import StockItemSerializer, StockQuantitySerializer
from .serializers import LocationSerializer
from .serializers import StockTrackingSerializer

from InvenTree.views import TreeSerializer

from rest_framework.serializers import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, response, filters, permissions


class StockCategoryTree(TreeSerializer):
    title = 'Stock'
    model = StockLocation


class StockDetail(generics.RetrieveUpdateDestroyAPIView):
    """

    get:
    Return a single StockItem object

    post:
    Update a StockItem

    delete:
    Remove a StockItem
    """

    queryset = StockItem.objects.all()
    serializer_class = StockItemSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class StockFilter(FilterSet):
    min_stock = NumberFilter(name='quantity', lookup_expr='gte')
    max_stock = NumberFilter(name='quantity', lookup_expr='lte')

    class Meta:
        model = StockItem
        fields = ['quantity', 'part', 'location']


class StockStocktake(APIView):
    """
    Stocktake API endpoint provides stock update of multiple items simultaneously
    The 'action' field tells the type of stock action to perform:
        * 'stocktake' - Count the stock item(s)
        * 'remove' - Remove the quantity provided from stock
        * 'add' - Add the quantity provided from stock
    """

    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
    ]

    def post(self, request, *args, **kwargs):

        if 'action' not in request.data:
            raise ValidationError({'action': 'Stocktake action must be provided'})

        action = request.data['action']

        ACTIONS = ['stocktake', 'remove', 'add']

        if action not in ACTIONS:
            raise ValidationError({'action': 'Action must be one of ' + ','.join(ACTIONS)})

        elif 'items[]' not in request.data:
            raise ValidationError({'items[]:' 'Request must contain list of items'})

        items = []

        # Ensure each entry is valid
        for entry in request.data['items[]']:
            if 'pk' not in entry:
                raise ValidationError({'pk': 'Each entry must contain pk field'})
            elif 'quantity' not in entry:
                raise ValidationError({'quantity': 'Each entry must contain quantity field'})

            item = {}
            try:
                item['item'] = StockItem.objects.get(pk=entry['pk'])
            except StockItem.DoesNotExist:
                raise ValidationError({'pk': 'No matching StockItem found for pk={pk}'.format(pk=entry['pk'])})
            try:
                item['quantity'] = int(entry['quantity'])
            except ValueError:
                raise ValidationError({'quantity': 'Quantity must be an integer'})

            if item['quantity'] < 0:
                raise ValidationError({'quantity': 'Quantity must be >= 0'})

            items.append(item)

        # Stocktake notes
        notes = ''

        if 'notes' in request.data:
            notes = request.data['notes']

        n = 0

        for item in items:
            quantity = int(item['quantity'])

            if action == u'stocktake':
                if item['item'].stocktake(quantity, request.user, notes=notes):
                    n += 1
            elif action == u'remove':
                if item['item'].take_stock(quantity, request.user, notes=notes):
                    n += 1
            elif action == u'add':
                if item['item'].add_stock(quantity, request.user, notes=notes):
                    n += 1

        return Response({'success': 'Updated stock for {n} items'.format(n=n)})


class StockMove(APIView):

    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
    ]

    def post(self, request, *args, **kwargs):

        data = request.data

        if u'location' not in data:
            raise ValidationError({'location': 'Destination must be specified'})

        loc_id = data.get(u'location')

        try:
            location = StockLocation.objects.get(pk=loc_id)
        except StockLocation.DoesNotExist:
            raise ValidationError({'location': 'Location does not exist'})

        if u'parts[]' not in data:
            raise ValidationError({'parts[]': 'Parts list must be specified'})

        part_list = data.get(u'parts[]')

        parts = []

        errors = []

        if u'notes' not in data:
            errors.append({'notes': 'Notes field must be supplied'})

        for pid in part_list:
            try:
                part = StockItem.objects.get(pk=pid)
                parts.append(part)
            except StockItem.DoesNotExist:
                errors.append({'part': 'Part {id} does not exist'.format(id=pid)})

        if len(errors) > 0:
            raise ValidationError(errors)

        n = 0

        for part in parts:
            if part.move(location, data.get('notes'), request.user):
                n += 1

        return Response({'success': 'Moved {n} parts to {loc}'.format(
            n=n,
            loc=str(location)
        )})


class StockLocationList(generics.ListCreateAPIView):

    queryset = StockLocation.objects.all()

    serializer_class = LocationSerializer

    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
    ]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filter_fields = [
        'parent',
    ]


class StockList(generics.ListCreateAPIView):
    """

    get:
    Return a list of all StockItem objects
    (with optional query filters)

    post:
    Create a new StockItem
    """

    def get_queryset(self):
        """
        If the query includes a particular location,
        we may wish to also request stock items from all child locations.
        This is set by the optional param 'include_child_categories'
        """

        # Does the client wish to filter by category?
        loc_id = self.request.query_params.get('location', None)

        # Start with all objects
        stock_list = StockItem.objects.all()

        if loc_id:
            location = get_object_or_404(StockLocation, pk=loc_id)

            # Filter by the supplied category
            flt = Q(location=loc_id)

            if self.request.query_params.get('include_child_locations', None):
                childs = location.getUniqueChildren()
                for child in childs:
                    # Ignore the top-level category (already filtered!)
                    if str(child) == str(loc_id):
                        continue
                    flt |= Q(location=child)

            stock_list = stock_list.filter(flt)

        return stock_list

    serializer_class = StockItemSerializer

    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
    ]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filter_fields = [
        'part',
        'uuid',
        'supplier_part',
        'customer',
        'belongs_to',
        # 'status' TODO - There are some issues filtering based on an enumeration field
    ]


class StockStocktakeEndpoint(generics.UpdateAPIView):

    queryset = StockItem.objects.all()
    serializer_class = StockQuantitySerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def update(self, request, *args, **kwargs):
        object = self.get_object()
        object.stocktake(request.data['quantity'], request.user)

        serializer = self.get_serializer(object)

        return response.Response(serializer.data)


class StockTrackingList(generics.ListCreateAPIView):

    queryset = StockItemTracking.objects.all()
    serializer_class = StockTrackingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

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
    """

    get:
    Return a single StockLocation object

    post:
    Update a StockLocation object

    delete:
    Remove a StockLocation object

    """

    queryset = StockLocation.objects.all()
    serializer_class = LocationSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


stock_endpoints = [
    url(r'^$', StockDetail.as_view(), name='stockitem-detail'),
]

location_endpoints = [
    url(r'^$', LocationDetail.as_view(), name='stocklocation-detail'),
]

stock_api_urls = [
    url(r'location/?', StockLocationList.as_view(), name='api-location-list'),

    url(r'location/(?P<pk>\d+)/', include(location_endpoints)),

    url(r'stocktake/?', StockStocktake.as_view(), name='api-stock-stocktake'),

    url(r'move/?', StockMove.as_view(), name='api-stock-move'),

    url(r'track/?', StockTrackingList.as_view(), name='api-stock-track'),

    url(r'^tree/?', StockCategoryTree.as_view(), name='api-stock-tree'),

    # Detail for a single stock item
    url(r'^(?P<pk>\d+)/', include(stock_endpoints)),

    url(r'^.*$', StockList.as_view(), name='api-stock-list'),
]
