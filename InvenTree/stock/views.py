"""
Django views for interacting with Stock app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.views.generic.edit import FormMixin
from django.views.generic import DetailView, ListView
from django.forms.models import model_to_dict
from django.forms import HiddenInput
from django.urls import reverse

from django.utils.translation import ugettext as _

from InvenTree.views import AjaxView
from InvenTree.views import AjaxUpdateView, AjaxDeleteView, AjaxCreateView
from InvenTree.views import QRCodeView

from InvenTree.helpers import str2bool, DownloadFile, GetExportFormats
from InvenTree.helpers import ExtractSerialNumbers
from datetime import datetime

from company.models import Company
from part.models import Part
from .models import StockItem, StockLocation, StockItemTracking

from .admin import StockItemResource

from .forms import EditStockLocationForm
from .forms import CreateStockItemForm
from .forms import EditStockItemForm
from .forms import AdjustStockForm
from .forms import TrackingEntryForm
from .forms import SerializeStockForm
from .forms import ExportOptionsForm


class StockIndex(ListView):
    """ StockIndex view loads all StockLocation and StockItem object
    """
    model = StockItem
    template_name = 'stock/location.html'
    context_obect_name = 'locations'

    def get_context_data(self, **kwargs):
        context = super(StockIndex, self).get_context_data(**kwargs).copy()

        # Return all top-level locations
        locations = StockLocation.objects.filter(parent=None)

        context['locations'] = locations
        context['items'] = StockItem.objects.all()

        context['loc_count'] = StockLocation.objects.count()
        context['stock_count'] = StockItem.objects.count()

        return context


class StockLocationDetail(DetailView):
    """
    Detailed view of a single StockLocation object
    """

    context_object_name = 'location'
    template_name = 'stock/location.html'
    queryset = StockLocation.objects.all()
    model = StockLocation


class StockItemDetail(DetailView):
    """
    Detailed view of a single StockItem object
    """

    context_object_name = 'item'
    template_name = 'stock/item.html'
    queryset = StockItem.objects.all()
    model = StockItem


class StockLocationEdit(AjaxUpdateView):
    """
    View for editing details of a StockLocation.
    This view is used with the EditStockLocationForm to deliver a modal form to the web view
    """

    model = StockLocation
    form_class = EditStockLocationForm
    context_object_name = 'location'
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Edit Stock Location'

    def get_form(self):
        """ Customize form data for StockLocation editing.

        Limit the choices for 'parent' field to those which make sense.
        """

        form = super(AjaxUpdateView, self).get_form()

        location = self.get_object()

        # Remove any invalid choices for the 'parent' field
        parent_choices = StockLocation.objects.all()
        parent_choices = parent_choices.exclude(id__in=location.getUniqueChildren())

        form.fields['parent'].queryset = parent_choices

        return form


class StockLocationQRCode(QRCodeView):
    """ View for displaying a QR code for a StockLocation object """

    ajax_form_title = "Stock Location QR code"

    def get_qr_data(self):
        """ Generate QR code data for the StockLocation """
        try:
            loc = StockLocation.objects.get(id=self.pk)
            return loc.format_barcode()
        except StockLocation.DoesNotExist:
            return None


class StockExportOptions(AjaxView):
    """ Form for selecting StockExport options """

    model = StockLocation
    ajax_form_title = 'Stock Export Options'
    form_class = ExportOptionsForm

    def post(self, request, *args, **kwargs):

        self.request = request

        fmt = request.POST.get('file_format', 'csv').lower()
        cascade = str2bool(request.POST.get('include_sublocations', False))

        # Format a URL to redirect to
        url = reverse('stock-export')

        url += '?format=' + fmt
        url += '&cascade=' + str(cascade)

        data = {
            'form_valid': True,
            'format': fmt,
            'cascade': cascade
        }

        return self.renderJsonResponse(self.request, self.form_class(), data=data)

    def get(self, request, *args, **kwargs):
        return self.renderJsonResponse(request, self.form_class())


class StockExport(AjaxView):
    """ Export stock data from a particular location.
    Returns a file containing stock information for that location.
    """

    model = StockItem

    def get(self, request, *args, **kwargs):

        export_format = request.GET.get('format', 'csv').lower()
        
        # Check if a particular location was specified
        loc_id = request.GET.get('location', None)
        location = None
        
        if loc_id:
            try:
                location = StockLocation.objects.get(pk=loc_id)
            except (ValueError, StockLocation.DoesNotExist):
                pass

        # Check if a particular supplier was specified
        sup_id = request.GET.get('supplier', None)
        supplier = None

        if sup_id:
            try:
                supplier = Company.objects.get(pk=sup_id)
            except (ValueError, Company.DoesNotExist):
                pass

        # Check if a particular part was specified
        part_id = request.GET.get('part', None)
        part = None

        if part_id:
            try:
                part = Part.objects.get(pk=part_id)
            except (ValueError, Part.DoesNotExist):
                pass

        if export_format not in GetExportFormats():
            export_format = 'csv'

        filename = 'InvenTree_Stocktake_{date}.{fmt}'.format(
            date=datetime.now().strftime("%d-%b-%Y"),
            fmt=export_format
        )

        if location:
            # CHeck if locations should be cascading
            cascade = str2bool(request.GET.get('cascade', True))
            stock_items = location.get_stock_items(cascade)
        else:
            cascade = True
            stock_items = StockItem.objects.all()

        if part:
            stock_items = stock_items.filter(part=part)

        if supplier:
            stock_items = stock_items.filter(supplier_part__supplier=supplier)

        # Filter out stock items that are not 'in stock'
        stock_items = stock_items.filter(customer=None)
        stock_items = stock_items.filter(belongs_to=None)

        # Pre-fetch related fields to reduce DB queries
        stock_items = stock_items.prefetch_related('part', 'supplier_part__supplier', 'location', 'purchase_order', 'build')

        dataset = StockItemResource().export(queryset=stock_items)

        filedata = dataset.export(export_format)

        return DownloadFile(filedata, filename)


class StockItemQRCode(QRCodeView):
    """ View for displaying a QR code for a StockItem object """

    ajax_form_title = "Stock Item QR Code"

    def get_qr_data(self):
        """ Generate QR code data for the StockItem """
        try:
            item = StockItem.objects.get(id=self.pk)
            return item.format_barcode()
        except StockItem.DoesNotExist:
            return None


class StockAdjust(AjaxView, FormMixin):
    """ View for enacting simple stock adjustments:
    
    - Take items from stock
    - Add items to stock
    - Count items
    - Move stock
    
    """

    ajax_template_name = 'stock/stock_adjust.html'
    ajax_form_title = 'Adjust Stock'
    form_class = AdjustStockForm
    stock_items = []

    def get_GET_items(self):
        """ Return list of stock items initally requested using GET.

        Items can be retrieved by:

        a) List of stock ID - stock[]=1,2,3,4,5
        b) Parent part - part=3
        c) Parent location - location=78
        d) Single item - item=2
        """

        # Start with all 'in stock' items
        items = StockItem.objects.filter(customer=None, belongs_to=None)

        # Client provides a list of individual stock items
        if 'stock[]' in self.request.GET:
            items = items.filter(id__in=self.request.GET.getlist('stock[]'))

        # Client provides a PART reference
        elif 'part' in self.request.GET:
            items = items.filter(part=self.request.GET.get('part'))

        # Client provides a LOCATION reference
        elif 'location' in self.request.GET:
            items = items.filter(location=self.request.GET.get('location'))

        # Client provides a single StockItem lookup
        elif 'item' in self.request.GET:
            items = [StockItem.objects.get(id=self.request.GET.get('item'))]

        # Unsupported query (no items)
        else:
            items = []

        for item in items:

            # Initialize quantity to zero for addition/removal
            if self.stock_action in ['take', 'add']:
                item.new_quantity = 0
            # Initialize quantity at full amount for counting or moving
            else:
                item.new_quantity = item.quantity

        return items

    def get_POST_items(self):
        """ Return list of stock items sent back by client on a POST request """

        items = []

        for item in self.request.POST:
            if item.startswith('stock-id-'):
                
                pk = item.replace('stock-id-', '')
                q = self.request.POST[item]

                try:
                    stock_item = StockItem.objects.get(pk=pk)
                except StockItem.DoesNotExist:
                    continue

                stock_item.new_quantity = q

                items.append(stock_item)

        return items

    def get_context_data(self):

        context = super().get_context_data()

        context['stock_items'] = self.stock_items

        context['stock_action'] = self.stock_action

        context['stock_action_title'] = self.stock_action.capitalize()

        return context

    def get_form(self):

        form = super().get_form()

        if not self.stock_action == 'move':
            form.fields.pop('destination')
            form.fields.pop('set_loc')

        return form

    def get(self, request, *args, **kwargs):

        self.request = request

        # Action
        self.stock_action = request.GET.get('action', '').lower()

        # Pick a default action...
        if self.stock_action not in ['move', 'count', 'take', 'add']:
            self.stock_action = 'count'

        # Choose the form title based on the action
        titles = {
            'move': 'Move Stock',
            'count': 'Count Stock',
            'take': 'Remove Stock',
            'add': 'Add Stock'
        }

        self.ajax_form_title = titles[self.stock_action]
        
        # Save list of items!
        self.stock_items = self.get_GET_items()

        return self.renderJsonResponse(request, self.get_form())

    def post(self, request, *args, **kwargs):

        self.request = request

        self.stock_action = request.POST.get('stock_action', 'invalid').lower()

        # Update list of stock items
        self.stock_items = self.get_POST_items()

        form = self.get_form()

        valid = form.is_valid()
        
        for item in self.stock_items:
            try:
                item.new_quantity = int(item.new_quantity)
            except ValueError:
                item.error = _('Must enter integer value')
                valid = False
                continue

            if item.new_quantity < 0:
                item.error = _('Quantity must be positive')
                valid = False
                continue

            if self.stock_action in ['move', 'take']:

                if item.new_quantity > item.quantity:
                    item.error = _('Quantity must not exceed {x}'.format(x=item.quantity))
                    valid = False
                    continue

        confirmed = str2bool(request.POST.get('confirm'))

        if not confirmed:
            valid = False
            form.errors['confirm'] = [_('Confirm stock adjustment')]

        data = {
            'form_valid': valid,
        }

        if valid:
            result = self.do_action()

            data['success'] = result

            # Special case - Single Stock Item
            # If we deplete the stock item, we MUST redirect to a new view
            single_item = len(self.stock_items) == 1

            if result and single_item:

                # Was the entire stock taken?
                item = self.stock_items[0]
                
                if item.quantity == 0:
                    # Instruct the form to redirect
                    data['url'] = reverse('stock-index')

        return self.renderJsonResponse(request, form, data=data)

    def do_action(self):
        """ Perform stock adjustment action """

        if self.stock_action == 'move':
            destination = None

            set_default_loc = str2bool(self.request.POST.get('set_loc', False))

            try:
                destination = StockLocation.objects.get(id=self.request.POST.get('destination'))
            except StockLocation.DoesNotExist:
                pass
            except ValueError:
                pass

            return self.do_move(destination, set_default_loc)

        elif self.stock_action == 'add':
            return self.do_add()

        elif self.stock_action == 'take':
            return self.do_take()

        elif self.stock_action == 'count':
            return self.do_count()

        else:
            return 'No action performed'

    def do_add(self):
        
        count = 0
        note = self.request.POST['note']

        for item in self.stock_items:
            if item.new_quantity <= 0:
                continue

            item.add_stock(item.new_quantity, self.request.user, notes=note)

            count += 1

        return _("Added stock to {n} items".format(n=count))

    def do_take(self):

        count = 0
        note = self.request.POST['note']

        for item in self.stock_items:
            if item.new_quantity <= 0:
                continue

            item.take_stock(item.new_quantity, self.request.user, notes=note)

            count += 1

        return _("Removed stock from {n} items".format(n=count))

    def do_count(self):
        
        count = 0
        note = self.request.POST['note']

        for item in self.stock_items:
            
            item.stocktake(item.new_quantity, self.request.user, notes=note)

            count += 1

        return _("Counted stock for {n} items".format(n=count))

    def do_move(self, destination, set_loc=None):
        """ Perform actual stock movement """

        count = 0

        note = self.request.POST['note']

        for item in self.stock_items:
            # Avoid moving zero quantity
            if item.new_quantity <= 0:
                continue

            # If we wish to set the destination location to the default one
            if set_loc:
                item.part.default_location = destination
                item.part.save()
            
            # Do not move to the same location (unless the quantity is different)
            if destination == item.location and item.new_quantity == item.quantity:
                continue

            item.move(destination, note, self.request.user, quantity=int(item.new_quantity))

            count += 1

        if count == 0:
            return _('No items were moved')
        
        else:
            return _('Moved {n} items to {dest}'.format(
                n=count,
                dest=destination.pathstring))


class StockItemEdit(AjaxUpdateView):
    """
    View for editing details of a single StockItem
    """

    model = StockItem
    form_class = EditStockItemForm
    context_object_name = 'item'
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Edit Stock Item'

    def get_form(self):
        """ Get form for StockItem editing.

        Limit the choices for supplier_part
        """

        form = super(AjaxUpdateView, self).get_form()

        item = self.get_object()

        # If the part cannot be purchased, hide the supplier_part field
        if not item.part.purchaseable:
            form.fields['supplier_part'].widget = HiddenInput()
        else:
            query = form.fields['supplier_part'].queryset
            query = query.filter(part=item.part.id)
            form.fields['supplier_part'].queryset = query

        if not item.part.trackable:
            form.fields.pop('serial')

        return form


class StockLocationCreate(AjaxCreateView):
    """
    View for creating a new StockLocation
    A parent location (another StockLocation object) can be passed as a query parameter
    """

    model = StockLocation
    form_class = EditStockLocationForm
    context_object_name = 'location'
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Create new Stock Location'

    def get_initial(self):
        initials = super(StockLocationCreate, self).get_initial().copy()

        loc_id = self.request.GET.get('location', None)

        if loc_id:
            try:
                initials['parent'] = StockLocation.objects.get(pk=loc_id)
            except StockLocation.DoesNotExist:
                pass

        return initials


class StockItemSerialize(AjaxUpdateView):
    """ View for manually serializing a StockItem """

    model = StockItem
    ajax_template_name = 'stock/item_serialize.html'
    ajax_form_title = 'Serialize Stock'
    form_class = SerializeStockForm

    def get_initial(self):

        initials = super().get_initial().copy()

        item = self.get_object()

        initials['quantity'] = item.quantity
        initials['destination'] = item.location.pk

        return initials

    def get(self, request, *args, **kwargs):
        
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):

        form = self.get_form()

        item = self.get_object()

        quantity = request.POST.get('quantity', 0)
        serials = request.POST.get('serial_numbers', '')
        dest_id = request.POST.get('destination', None)
        notes = request.POST.get('note', '')
        user = request.user

        valid = True

        try:
            destination = StockLocation.objects.get(pk=dest_id)
        except (ValueError, StockLocation.DoesNotExist):
            destination = None

        try:
            numbers = ExtractSerialNumbers(serials, quantity)
        except ValidationError as e:
            form.errors['serial_numbers'] = e.messages
            valid = False
            numbers = []
        
        if valid:
            try:
                item.serializeStock(quantity, numbers, user, notes=notes, location=destination)
            except ValidationError as e:
                messages = e.message_dict
                
                for k in messages.keys():
                    if k in ['quantity', 'destination', 'serial_numbers']:
                        form.errors[k] = messages[k]
                    else:
                        form.non_field_errors = messages[k]

                valid = False

        data = {
            'form_valid': valid,
        }

        return self.renderJsonResponse(request, form, data=data)


class StockItemCreate(AjaxCreateView):
    """
    View for creating a new StockItem
    Parameters can be pre-filled by passing query items:
    - part: The part of which the new StockItem is an instance
    - location: The location of the new StockItem

    If the parent part is a "tracked" part, provide an option to create uniquely serialized items
    rather than a bulk quantity of stock items
    """

    model = StockItem
    form_class = CreateStockItemForm
    context_object_name = 'item'
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Create new Stock Item'

    def get_form(self):
        """ Get form for StockItem creation.
        Overrides the default get_form() method to intelligently limit
        ForeignKey choices based on other selections
        """

        form = super().get_form()

        # If the user has selected a Part, limit choices for SupplierPart
        if form['part'].value():
            part_id = form['part'].value()

            try:
                part = Part.objects.get(id=part_id)
                
                # Hide the 'part' field (as a valid part is selected)
                form.fields['part'].widget = HiddenInput()

                # trackable parts get special consideration
                if part.trackable:
                    form.fields['delete_on_deplete'].widget = HiddenInput()
                    form.fields['delete_on_deplete'].initial = False
                else:
                    form.fields.pop('serial_numbers')

                # If the part is NOT purchaseable, hide the supplier_part field
                if not part.purchaseable:
                    form.fields['supplier_part'].widget = HiddenInput()
                else:
                    # Pre-select the allowable SupplierPart options
                    parts = form.fields['supplier_part'].queryset
                    parts = parts.filter(part=part.id)

                    form.fields['supplier_part'].queryset = parts

                    # If there is one (and only one) supplier part available, pre-select it
                    all_parts = parts.all()
                    if len(all_parts) == 1:

                        # TODO - This does NOT work for some reason? Ref build.views.BuildItemCreate
                        form.fields['supplier_part'].initial = all_parts[0].id

            except Part.DoesNotExist:
                pass

        # Otherwise if the user has selected a SupplierPart, we know what Part they meant!
        elif form['supplier_part'].value() is not None:
            pass

        return form

    def get_initial(self):
        """ Provide initial data to create a new StockItem object
        """

        # Is the client attempting to copy an existing stock item?
        item_to_copy = self.request.GET.get('copy', None)

        if item_to_copy:
            try:
                original = StockItem.objects.get(pk=item_to_copy)
                initials = model_to_dict(original)
                self.ajax_form_title = "Copy Stock Item"
            except StockItem.DoesNotExist:
                initials = super(StockItemCreate, self).get_initial().copy()

        else:
            initials = super(StockItemCreate, self).get_initial().copy()

        part_id = self.request.GET.get('part', None)
        loc_id = self.request.GET.get('location', None)

        # Part field has been specified
        if part_id:
            try:
                part = Part.objects.get(pk=part_id)
                initials['part'] = part
                initials['location'] = part.get_default_location()
                initials['supplier_part'] = part.default_supplier
            except Part.DoesNotExist:
                pass

        # Location has been specified
        if loc_id:
            try:
                initials['location'] = StockLocation.objects.get(pk=loc_id)
            except StockLocation.DoesNotExist:
                pass

        return initials

    def post(self, request, *args, **kwargs):
        """ Handle POST of StockItemCreate form.

        - Manage serial-number valdiation for tracked parts
        """

        form = self.get_form()

        data = {}

        valid = form.is_valid()

        if valid:
            part_id = form['part'].value()
            try:
                part = Part.objects.get(id=part_id)
                quantity = int(form['quantity'].value())
            except (Part.DoesNotExist, ValueError):
                part = None
                quantity = 1
                valid = False

            if part is None:
                form.errors['part'] = [_('Invalid part selection')]
            else:
                # A trackable part must provide serial numbesr
                if part.trackable:
                    sn = request.POST.get('serial_numbers', '')

                    sn = str(sn).strip()

                    # If user has specified a range of serial numbers
                    if len(sn) > 0:
                        try:
                            serials = ExtractSerialNumbers(sn, quantity)

                            existing = []

                            for serial in serials:
                                if not StockItem.check_serial_number(part, serial):
                                    existing.append(serial)

                            if len(existing) > 0:
                                exists = ",".join([str(x) for x in existing])
                                form.errors['serial_numbers'] = [_('The following serial numbers already exist: ({sn})'.format(sn=exists))]
                                valid = False

                            # At this point we have a list of serial numbers which we know are valid,
                            # and do not currently exist
                            form.clean()

                            data = form.cleaned_data

                            for serial in serials:
                                # Create a new stock item for each serial number
                                item = StockItem(
                                    part=part,
                                    quantity=1,
                                    serial=serial,
                                    supplier_part=data.get('supplier_part'),
                                    location=data.get('location'),
                                    batch=data.get('batch'),
                                    delete_on_deplete=False,
                                    status=data.get('status'),
                                    notes=data.get('notes'),
                                    URL=data.get('URL'),
                                )

                                item.save(user=request.user)

                        except ValidationError as e:
                            form.errors['serial_numbers'] = e.messages
                            valid = False

                else:
                    # For non-serialized items, simply save the form.
                    # We need to call _post_clean() here because it is prevented in the form implementation
                    form.clean()
                    form._post_clean()
                    
                    item = form.save(commit=False)
                    item.save(user=request.user)

                    data['pk'] = item.pk
                    data['url'] = item.get_absolute_url()
                    data['success'] = _("Created new stock item")

        data['form_valid'] = valid

        return self.renderJsonResponse(request, form, data=data)


class StockLocationDelete(AjaxDeleteView):
    """
    View to delete a StockLocation
    Presents a deletion confirmation form to the user
    """

    model = StockLocation
    success_url = '/stock'
    ajax_template_name = 'stock/location_delete.html'
    context_object_name = 'location'
    ajax_form_title = 'Delete Stock Location'


class StockItemDelete(AjaxDeleteView):
    """
    View to delete a StockItem
    Presents a deletion confirmation form to the user
    """

    model = StockItem
    success_url = '/stock/'
    ajax_template_name = 'stock/item_delete.html'
    context_object_name = 'item'
    ajax_form_title = 'Delete Stock Item'


class StockItemTrackingDelete(AjaxDeleteView):
    """
    View to delete a StockItemTracking object
    Presents a deletion confirmation form to the user
    """

    model = StockItemTracking
    ajax_template_name = 'stock/tracking_delete.html'
    ajax_form_title = 'Delete Stock Tracking Entry'


class StockTrackingIndex(ListView):
    """
    StockTrackingIndex provides a page to display StockItemTracking objects
    """

    model = StockItemTracking
    template_name = 'stock/tracking.html'
    context_object_name = 'items'


class StockItemTrackingEdit(AjaxUpdateView):
    """ View for editing a StockItemTracking object """

    model = StockItemTracking
    ajax_form_title = 'Edit Stock Tracking Entry'
    form_class = TrackingEntryForm


class StockItemTrackingCreate(AjaxCreateView):
    """ View for creating a new StockItemTracking object.
    """

    model = StockItemTracking
    ajax_form_title = "Add Stock Tracking Entry"
    form_class = TrackingEntryForm

    def post(self, request, *args, **kwargs):

        self.request = request
        self.form = self.get_form()

        valid = False

        if self.form.is_valid():
            stock_id = self.kwargs['pk']

            if stock_id:
                try:
                    stock_item = StockItem.objects.get(id=stock_id)

                    # Save new tracking information
                    tracking = self.form.save(commit=False)
                    tracking.item = stock_item
                    tracking.user = self.request.user
                    tracking.quantity = stock_item.quantity
                    tracking.date = datetime.now().date()
                    tracking.system = False

                    tracking.save()

                    valid = True

                except (StockItem.DoesNotExist, ValueError):
                    pass

        data = {
            'form_valid': valid
        }

        return self.renderJsonResponse(request, self.form, data=data)
