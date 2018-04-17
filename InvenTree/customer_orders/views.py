from django.views.generic import DetailView, ListView

from .models import CustomerOrder

class CustomerOrderIndex(ListView):
    model = CustomerOrder
    template_name = 'customer_orders/index.html'
    context_object_name = 'customer_orders'
