from django.conf.urls import url, include
from InvenTree.helpers import str2bool

from basket.models import SalesOrderBasket
from basket.serializers import SOBasketSerializer

from django_filters import rest_framework as rest_filters
from rest_framework import generics
from rest_framework import filters, status
from rest_framework.response import Response
from rest_framework.serializers import ValidationError


class BasketList(generics.ListCreateAPIView):
    """
    API endpoint for accessing a list of SalesOrder objects.

    - GET: Return list of SO objects (with filters)
    - POST: Create a new SalesOrder
    """

    queryset = SalesOrderBasket.objects.all()
    serializer_class = SOBasketSerializer

    def create(self, request, *args, **kwargs):
        """
        Save user information on create
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        item = serializer.save()
        item.created_by = request.user
        item.save()

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_serializer(self, *args, **kwargs):

        try:
            kwargs['customer_detail'] = str2bool(self.request.query_params.get('customer_detail', False))
        except AttributeError:
            pass

        # Ensure the context is passed through to the serializer
        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

    def get_queryset(self, *args, **kwargs):

        queryset = super().get_queryset(*args, **kwargs)

        queryset = queryset.prefetch_related(
            'orders',
        )

        queryset = SOBasketSerializer.annotate_queryset(queryset)

        return queryset

    def filter_queryset(self, queryset):
        """
        Perform custom filtering operations on the SalesOrder queryset.
        """

        queryset = super().filter_queryset(queryset)

        params = self.request.query_params

        # Filter by 'outstanding' status
        # outstanding = params.get('outstanding', None)

        # if outstanding is not None:
        #     outstanding = str2bool(outstanding)

        #     if outstanding:
        #         queryset = queryset.filter(status__in=SalesOrderStatus.OPEN)
        #     else:
        #         queryset = queryset.exclude(status__in=SalesOrderStatus.OPEN)

        # # Filter by 'overdue' status
        # overdue = params.get('overdue', None)

        # if overdue is not None:
        #     overdue = str2bool(overdue)

        #     if overdue:
        #         queryset = queryset.filter(SalesOrder.OVERDUE_FILTER)
        #     else:
        #         queryset = queryset.exclude(SalesOrder.OVERDUE_FILTER)

        status = params.get('status', None)

        if status is not None:
            queryset = queryset.filter(status=status)

        # Filter by "Part"
        # Only return SalesOrder which have LineItem referencing the part
        # part = params.get('part', None)

        # if part is not None:
        #     try:
        #         part = Part.objects.get(pk=part)
        #         queryset = queryset.filter(id__in=[so.id for so in part.sales_orders()])
        #     except (Part.DoesNotExist, ValueError):
        #         pass

        # Filter by 'date range'
        # min_date = params.get('min_date', None)
        # max_date = params.get('max_date', None)

        # if min_date is not None and max_date is not None:
        #     queryset = SalesOrder.filterByDate(queryset, min_date, max_date)

        return queryset

    filter_backends = [
        rest_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filter_fields = [
        'order',
    ]

    ordering_fields = [
        'name',
        'status',
        'orders',
    ]

    search_fields = [
        'name',
        'status',
        'orders',
    ]

    ordering = '-creation_date'


class BasketDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for detail view of a SalesOrder object.
    """

    queryset = SalesOrderBasket.objects.all()
    serializer_class = SOBasketSerializer

    def get_serializer(self, *args, **kwargs):

        try:
            kwargs['customer_detail'] = str2bool(self.request.query_params.get('customer_detail', False))
        except AttributeError:
            pass

        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

    def get_queryset(self, *args, **kwargs):

        queryset = super().get_queryset(*args, **kwargs)

        queryset = queryset.prefetch_related('orders')

        queryset = SOBasketSerializer.annotate_queryset(queryset)

        return queryset

basket_api_urls = [
    # API endpoints for baskets
    url(r'^b/', include([
        url(r'^(?P<pk>\d+)/$', BasketDetail.as_view(), name='api-basket-detail'),
        url(r'^.*$', BasketList.as_view(), name='api-basket-list'),
    ])),
]