from django.conf.urls import url, include
from InvenTree.helpers import str2bool

from basket.models import SalesOrderBasket
from basket.serializers import SOBasketSerializer

from django_filters import rest_framework as rest_filters
from rest_framework import generics
from rest_framework.decorators import action, permission_classes
from rest_framework import filters, status
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView
from rest_framework import permissions



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
        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

    def get_queryset(self, *args, **kwargs):

        queryset = super().get_queryset(*args, **kwargs)
        print(queryset)
        queryset = queryset.prefetch_related(
            'sales_orders',
        )

        # queryset = SOBasketSerializer.annotate_queryset(queryset)

        return queryset

    def filter_queryset(self, queryset):
        """
        Perform custom filtering operations on the SalesOrder queryset.
        """

        queryset = super().filter_queryset(queryset)

        params = self.request.query_params

        status = params.get('status', None)

        if status is not None:
            queryset = queryset.filter(status=status)

        return queryset

    filter_backends = [
        rest_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filter_fields = [
       
    ]

    ordering_fields = [
        'name',
        'status',
    ]

    search_fields = [
        'name',
        'status',
    ]

    ordering = '-creation_date'


class BasketDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for detail view of a Basket object.
    """

    queryset = SalesOrderBasket.objects.all()
    serializer_class = SOBasketSerializer

    def get_queryset(self, *args, **kwargs):

        queryset = super().get_queryset(*args, **kwargs)
        queryset = queryset.prefetch_related('sales_orders')
        return queryset

@permission_classes((permissions.IsAuthenticated,))
class AddOrderToBasket(APIView):

    """For allow post method """
    def post(self, request):
        try:
            basket = SalesOrderBasket.objects.filter(pk=request.data.get('basket', None)).first()
            order_id = request.data.get('order', None)
            basket.add_order(order_id["pk"])
            # serializer = self.get_serializer(basket, many=True)
            # return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception:
            print(Exception)
            return Response('Error while adding order to basket')
        return Response()
   

basket_api_urls = [
    # API endpoints for baskets
    url(r'^(?P<pk>\d+/?)', BasketDetail.as_view(), name='api-basket-detail'),
    url(r'^scan/', AddOrderToBasket.as_view(), name='api-basket-addorder'),
    url(r'^.*$', BasketList.as_view(), name='api-basket-list'),
]