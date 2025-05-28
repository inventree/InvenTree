# inven_tree_custom/dispatch/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin # For access control
from django.contrib.auth.decorators import login_required # For function-based views
from django.contrib import messages # For user feedback
from django.http import HttpResponseRedirect
from django.db import transaction # For atomic operations

from .models import Dispatch, DispatchItem
from .forms import DispatchForm, AddStockItemToDispatchForm
from .utils import get_dispatch_summary_data

# Ensure StockItem is imported - this is critical
# The exact path might vary based on InvenTree version.
# Common paths: 'stock.models.StockItem' or 'inventree.stock.models.StockItem'
try:
    from stock.models import StockItem
except ImportError:
    # Fallback or log, but this is essential for the functionality
    StockItem = None 
    print("WARNING: Could not import StockItem model in inventree_custom/dispatch/views.py")


class DispatchListView(LoginRequiredMixin, ListView):
    model = Dispatch
    template_name = 'inventree_custom/dispatch/dispatch_list.html' # Path within plugin's templates
    context_object_name = 'dispatches'
    paginate_by = 20 # Optional: if you expect many dispatches

    def get_queryset(self):
        return Dispatch.objects.all().order_by('-date', '-created_at')

class DispatchDetailView(LoginRequiredMixin, DetailView):
    model = Dispatch
    template_name = 'inventree_custom/dispatch/dispatch_detail.html'
    context_object_name = 'dispatch'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dispatch = self.get_object()
        context['items'] = dispatch.items.all().select_related('stock_item') # Optimize query
        context['add_item_form'] = AddStockItemToDispatchForm() # For adding new items
        
        # Calculate and add summary data
        context['summary_data'] = get_dispatch_summary_data(dispatch) # <-- Call the function
        return context

class DispatchCreateView(LoginRequiredMixin, CreateView):
    model = Dispatch
    form_class = DispatchForm
    template_name = 'inventree_custom/dispatch/dispatch_form.html'
    
    def get_success_url(self):
        # Redirect to the detail view of the newly created dispatch
        messages.success(self.request, "Dispatch created successfully.")
        return reverse_lazy('plugin:inventreecustom:dispatch_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        # You can add logic here if needed, e.g., setting a creator user
        # form.instance.created_by = self.request.user
        return super().form_valid(form)

class DispatchUpdateView(LoginRequiredMixin, UpdateView):
    model = Dispatch
    form_class = DispatchForm
    template_name = 'inventree_custom/dispatch/dispatch_form.html'

    def get_success_url(self):
        messages.success(self.request, "Dispatch updated successfully.")
        return reverse_lazy('plugin:inventreecustom:dispatch_detail', kwargs={'pk': self.object.pk})

# Placeholder for the view function/method to add a stock item to a dispatch
# This will be fleshed out in a later step (Scanning Workflow)
# For now, it's useful to have the AddStockItemToDispatchForm in DispatchDetailView context.

# ... (Class-based views: DispatchListView, DispatchDetailView, DispatchCreateView, DispatchUpdateView) ...
# (These should already be present from previous steps)


@login_required
@transaction.atomic # Ensure database operations are atomic
def add_item_to_dispatch(request, dispatch_pk):
    dispatch = get_object_or_404(Dispatch, pk=dispatch_pk)
    
    if request.method == 'POST':
        form = AddStockItemToDispatchForm(request.POST)
        if form.is_valid():
            product_number_input = form.cleaned_data['product_number']
            quantity_to_add = form.cleaned_data['quantity']

            if StockItem is None:
                messages.error(request, "StockItem model not available. Cannot add item.")
                return HttpResponseRedirect(reverse('plugin:inventreecustom:dispatch_detail', kwargs={'pk': dispatch_pk}))

            try:
                # Assuming the 'product_number' field we created on StockItem is the target for scanning
                stock_item_instance = StockItem.objects.get(product_number=product_number_input)
                
                # Check if item is already in this dispatch
                dispatch_item, created = DispatchItem.objects.get_or_create(
                    dispatch=dispatch,
                    stock_item=stock_item_instance,
                    defaults={'quantity': quantity_to_add}
                )

                if not created:
                    # Item already exists, update quantity
                    dispatch_item.quantity += quantity_to_add 
                    dispatch_item.save()
                    messages.info(request, f"Item {stock_item_instance.product_number} quantity updated to {dispatch_item.quantity}.")
                else:
                    messages.success(request, f"Item {stock_item_instance.product_number} added successfully.")

            except StockItem.DoesNotExist:
                messages.error(request, f"Stock item with Product Number '{product_number_input}' not found.")
            except Exception as e: # Catch other potential errors e.g. database errors, multiple items returned if PN not unique
                messages.error(request, f"Could not add item: {str(e)}")
        else:
            # Form validation errors (e.g. quantity is not a number)
            # Collect form errors to display them
            error_list = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_list.append(f"{field.capitalize()}: {error}")
            messages.error(request, "Invalid data: " + "; ".join(error_list))
            
        return HttpResponseRedirect(reverse('plugin:inventreecustom:dispatch_detail', kwargs={'pk': dispatch_pk}))
    else:
        # Should not be reached if form is on detail page and method is POST
        return redirect('plugin:inventreecustom:dispatch_detail', pk=dispatch_pk)
