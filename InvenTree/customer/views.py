from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect

from django.views.generic import DetailView, ListView
from django.views.generic.edit import UpdateView, DeleteView, CreateView

from .models import Customer, CustomerOrder


class CustomerIndex(ListView):
    model = Customer
    template_name = 'customer/index.html'
    context_obect_name = 'customers'


class CustomerOrderIndex(ListView):
    model = CustomerOrder
    template_name = 'customer/order_index.html'
    context_object_name = 'customer_orders'


class CustomerDetail(DetailView):
    model = Customer
    template_name = 'customer/detail.html'
    queryset = Customer.objects.all()
    context_object_name = 'customer'


class CustomerOrderDetail(DetailView):
    model = CustomerOrder
    template_name = 'customer/order_detail.html'
    queryset = CustomerOrder.objects.all()
    context_object_name = 'order'
