"""
Django views for interacting with Stock app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.views.generic.edit import FormMixin
from django.views.generic import DetailView, ListView, UpdateView
from django.forms.models import model_to_dict
from django.forms import HiddenInput
from django.urls import reverse

from django.utils.translation import ugettext as _

from InvenTree.views import AjaxView
from InvenTree.views import AjaxUpdateView, AjaxDeleteView, AjaxCreateView
from InvenTree.views import QRCodeView
from InvenTree.forms import ConfirmForm

from InvenTree.helpers import str2bool, DownloadFile, GetExportFormats
from InvenTree.helpers import ExtractSerialNumbers

from decimal import Decimal, InvalidOperation
from datetime import datetime

from company.models import Company, SupplierPart
from part.models import Part
from report.models import TestReport
from label.models import StockItemLabel
from .models import StockItem, StockLocation, StockItemTracking, StockItemAttachment, StockItemTestResult

from .admin import StockItemResource

from . import forms as StockForms


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


class StockItemNotes(UpdateView):
    """ View for editing the 'notes' field of a StockItem object """

    context_object_name = 'item'
    template_name = 'stock/item_notes.html'
    model = StockItem

    fields = ['notes']

    def get_success_url(self):
        return reverse('stock-item-notes', kwargs={'pk': self.get_object().id})

    def get_context_data(self, **kwargs):

        ctx = super().get_context_data(**kwargs)

        ctx['editing'] = str2bool(self.request.GET.get('edit', ''))

        return ctx


class StockLocationEdit(AjaxUpdateView):
    """
    View for editing details of a StockLocation.
    This view is used with the EditStockLocationForm to deliver a modal form to the web view
    """

    model = StockLocation
    form_class = StockForms.EditStockLocationForm
    context_object_name = 'location'
    ajax_template_name = 'modal_form.html'
    ajax_form_title = _('Edit Stock Location')

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

    ajax_form_title = _("Stock Location QR code")

    def get_qr_data(self):
        """ Generate QR code data for the StockLocation """
        try:
            loc = StockLocation.objects.get(id=self.pk)
            return loc.format_barcode()
        except StockLocation.DoesNotExist:
            return None


class StockItemAttachmentCreate(AjaxCreateView):
    """
    View for adding a new attachment for a StockItem
    """

    model = StockItemAttachment
    form_class = StockForms.EditStockItemAttachmentForm
    ajax_form_title = _("Add Stock Item Attachment")
    ajax_template_name = "modal_form.html"

    def post_save(self, **kwargs):
        """ Record the user that uploaded the attachment """
        
        self.object.user = self.request.user
        self.object.save()

    def get_data(self):
        return {
            'success': _("Added attachment")
        }

    def get_initial(self):
        """
        Get initial data for the new StockItem attachment object.

        - Client must provide a valid StockItem ID
        """

        initials = super().get_initial()

        try:
            initials['stock_item'] = StockItem.objects.get(id=self.request.GET.get('item', None))
        except (ValueError, StockItem.DoesNotExist):
            pass

        return initials

    def get_form(self):

        form = super().get_form()
        form.fields['stock_item'].widget = HiddenInput()
        
        return form


class StockItemAttachmentEdit(AjaxUpdateView):
    """
    View for editing a StockItemAttachment object.
    """

    model = StockItemAttachment
    form_class = StockForms.EditStockItemAttachmentForm
    ajax_form_title = _("Edit Stock Item Attachment")

    def get_form(self):

        form = super().get_form()
        form.fields['stock_item'].widget = HiddenInput()

        return form


class StockItemAttachmentDelete(AjaxDeleteView):
    """
    View for deleting a StockItemAttachment object.
    """

    model = StockItemAttachment
    ajax_form_title = _("Delete Stock Item Attachment")
    ajax_template_name = "attachment_delete.html"
    context_object_name = "attachment"

    def get_data(self):
        return {
            'danger': _("Deleted attachment"),
        }


class StockItemAssignToCustomer(AjaxUpdateView):
    """
    View for manually assigning a StockItem to a Customer
    """

    model = StockItem
    ajax_form_title = _("Assign to Customer")
    context_object_name = "item"
    form_class = StockForms.AssignStockItemToCustomerForm

    def post(self, request, *args, **kwargs):

        customer = request.POST.get('customer', None)

        if customer:
            try:
                customer = Company.objects.get(pk=customer)
            except (ValueError, Company.DoesNotExist):
                customer = None

        if customer is not None:
            stock_item = self.get_object()

            item = stock_item.allocateToCustomer(
                customer,
                user=request.user
            )

            item.clearAllocations()

        data = {
            'form_valid': True,
        }

        return self.renderJsonResponse(request, self.get_form(), data)


class StockItemReturnToStock(AjaxUpdateView):
    """
    View for returning a stock item (which is assigned to a customer) to stock.
    """

    model = StockItem
    ajax_form_title = _("Return to Stock")
    context_object_name = "item"
    form_class = StockForms.ReturnStockItemForm

    def post(self, request, *args, **kwargs):

        location = request.POST.get('location', None)

        if location:
            try:
                location = StockLocation.objects.get(pk=location)
            except (ValueError, StockLocation.DoesNotExist):
                location = None

        if location:
            stock_item = self.get_object()

            stock_item.returnFromCustomer(location, request.user)
        else:
            raise ValidationError({'location': _("Specify a valid location")})

        data = {
            'form_valid': True,
            'success': _("Stock item returned from customer")
        }

        return self.renderJsonResponse(request, self.get_form(), data)


class StockItemSelectLabels(AjaxView):
    """
    View for selecting a template for printing labels for one (or more) StockItem objects
    """

    model = StockItem
    ajax_form_title = _('Select Label Template')

    def get_form(self):

        item = StockItem.objects.get(pk=self.kwargs['pk'])

        labels = []

        # Construct a list of StockItemLabel objects which are enabled, and the filters match the selected StockItem
        for label in StockItemLabel.objects.filter(enabled=True):
            if label.matches_stock_item(item):
                labels.append(label)

        return StockForms.StockItemLabelSelectForm(labels)

    def post(self, request, *args, **kwargs):

        label = request.POST.get('label', None)

        try:
            label = StockItemLabel.objects.get(pk=label)
        except (ValueError, StockItemLabel.DoesNotExist):
            raise ValidationError({'label': _("Select valid label")})
    
        stock_item = StockItem.objects.get(pk=self.kwargs['pk'])

        url = reverse('stock-item-print-labels')

        url += '?label={pk}'.format(pk=label.pk)
        url += '&items[]={pk}'.format(pk=stock_item.pk)

        data = {
            'form_valid': True,
            'url': url,
        }

        return self.renderJsonResponse(request, self.get_form(), data=data)


class StockItemPrintLabels(AjaxView):
    """
    View for printing labels and returning a PDF

    Requires the following arguments to be passed as URL params:

    items: List of valid StockItem pk values
    label: Valid pk of a StockItemLabel template
    """

    def get(self, request, *args, **kwargs):

        label = request.GET.get('label', None)

        try:
            label = StockItemLabel.objects.get(pk=label)
        except (ValueError, StockItemLabel.DoesNotExist):
            raise ValidationError({'label': 'Invalid label ID'})

        item_pks = request.GET.getlist('items[]')

        items = []

        for pk in item_pks:
            try:
                item = StockItem.objects.get(pk=pk)
                items.append(item)
            except (ValueError, StockItem.DoesNotExist):
                pass

        if len(items) == 0:
            raise ValidationError({'items': 'Must provide valid stockitems'})

        pdf = label.render(items).getbuffer()

        return DownloadFile(pdf, 'stock_labels.pdf', content_type='application/pdf')


class StockItemDeleteTestData(AjaxUpdateView):
    """
    View for deleting all test data
    """

    model = StockItem
    form_class = ConfirmForm
    ajax_form_title = _("Delete All Test Data")

    def get_form(self):
        return ConfirmForm()

    def post(self, request, *args, **kwargs):

        valid = False

        stock_item = StockItem.objects.get(pk=self.kwargs['pk'])
        form = self.get_form()
        
        confirm = str2bool(request.POST.get('confirm', False))

        if confirm is not True:
            form.errors['confirm'] = [_('Confirm test data deletion')]
            form.non_field_errors = [_('Check the confirmation box')]
        else:
            stock_item.test_results.all().delete()
            valid = True

        data = {
            'form_valid': valid,
        }

        return self.renderJsonResponse(request, form, data)


class StockItemTestResultCreate(AjaxCreateView):
    """
    View for adding a new StockItemTestResult
    """

    model = StockItemTestResult
    form_class = StockForms.EditStockItemTestResultForm
    ajax_form_title = _("Add Test Result")

    def post_save(self, **kwargs):
        """ Record the user that uploaded the test result """

        self.object.user = self.request.user
        self.object.save()

    def get_initial(self):

        initials = super().get_initial()

        try:
            stock_id = self.request.GET.get('stock_item', None)
            initials['stock_item'] = StockItem.objects.get(pk=stock_id)
        except (ValueError, StockItem.DoesNotExist):
            pass

        initials['test'] = self.request.GET.get('test', '')

        return initials

    def get_form(self):

        form = super().get_form()
        form.fields['stock_item'].widget = HiddenInput()

        return form


class StockItemTestResultEdit(AjaxUpdateView):
    """
    View for editing a StockItemTestResult
    """

    model = StockItemTestResult
    form_class = StockForms.EditStockItemTestResultForm
    ajax_form_title = _("Edit Test Result")

    def get_form(self):

        form = super().get_form()

        form.fields['stock_item'].widget = HiddenInput()
        
        return form


class StockItemTestResultDelete(AjaxDeleteView):
    """
    View for deleting a StockItemTestResult
    """

    model = StockItemTestResult
    ajax_form_title = _("Delete Test Result")
    context_object_name = "result"


class StockItemTestReportSelect(AjaxView):
    """
    View for selecting a TestReport template,
    and generating a TestReport as a PDF.
    """

    model = StockItem
    ajax_form_title = _("Select Test Report Template")

    def get_form(self):

        stock_item = StockItem.objects.get(pk=self.kwargs['pk'])
        return StockForms.TestReportFormatForm(stock_item)

    def post(self, request, *args, **kwargs):

        template_id = request.POST.get('template', None)

        try:
            template = TestReport.objects.get(pk=template_id)
        except (ValueError, TestReport.DoesNoteExist):
            raise ValidationError({'template': _("Select valid template")})

        stock_item = StockItem.objects.get(pk=self.kwargs['pk'])

        url = reverse('stock-item-test-report-download')

        url += '?stock_item={id}'.format(id=stock_item.pk)
        url += '&template={id}'.format(id=template.pk)

        data = {
            'form_valid': True,
            'url': url,
        }

        return self.renderJsonResponse(request, self.get_form(), data=data)


class StockItemTestReportDownload(AjaxView):
    """
    Download a TestReport against a StockItem.

    Requires the following arguments to be passed as URL params:

    stock_item - Valid PK of a StockItem object
    template - Valid PK of a TestReport template object

    """

    def get(self, request, *args, **kwargs):

        template = request.GET.get('template', None)
        stock_item = request.GET.get('stock_item', None)

        try:
            template = TestReport.objects.get(pk=template)
        except (ValueError, TestReport.DoesNotExist):
            raise ValidationError({'template': 'Invalid template ID'})

        try:
            stock_item = StockItem.objects.get(pk=stock_item)
        except (ValueError, StockItem.DoesNotExist):
            raise ValidationError({'stock_item': 'Invalid StockItem ID'})

        template.stock_item = stock_item

        return template.render(request)


class StockExportOptions(AjaxView):
    """ Form for selecting StockExport options """

    model = StockLocation
    ajax_form_title = _('Stock Export Options')
    form_class = StockForms.ExportOptionsForm

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

        # Check if a particular supplier_part was specified
        sup_part_id = request.GET.get('supplier_part', None)
        supplier_part = None

        if sup_part_id:
            try:
                supplier_part = SupplierPart.objects.get(pk=sup_part_id)
            except (ValueError, SupplierPart.DoesNotExist):
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

        if supplier_part:
            stock_items = stock_items.filter(supplier_part=supplier_part)

        # Filter out stock items that are not 'in stock'
        stock_items = stock_items.filter(StockItem.IN_STOCK_FILTER)

        # Pre-fetch related fields to reduce DB queries
        stock_items = stock_items.prefetch_related('part', 'supplier_part__supplier', 'location', 'purchase_order', 'build')

        dataset = StockItemResource().export(queryset=stock_items)

        filedata = dataset.export(export_format)

        return DownloadFile(filedata, filename)


class StockItemQRCode(QRCodeView):
    """ View for displaying a QR code for a StockItem object """

    ajax_form_title = _("Stock Item QR Code")

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
    - Delete stock items
    
    """

    ajax_template_name = 'stock/stock_adjust.html'
    ajax_form_title = _('Adjust Stock')
    form_class = StockForms.AdjustStockForm
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
        items = StockItem.objects.filter(StockItem.IN_STOCK_FILTER)

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

        context['stock_action'] = self.stock_action.strip().lower()

        context['stock_action_title'] = self.stock_action.capitalize()

        # Quantity column will be read-only in some circumstances
        context['edit_quantity'] = not self.stock_action == 'delete'

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
        if self.stock_action not in ['move', 'count', 'take', 'add', 'delete']:
            self.stock_action = 'count'

        # Choose the form title based on the action
        titles = {
            'move': _('Move Stock Items'),
            'count': _('Count Stock Items'),
            'take': _('Remove From Stock'),
            'add': _('Add Stock Items'),
            'delete': _('Delete Stock Items')
        }

        self.ajax_form_title = titles[self.stock_action]
        
        # Save list of items!
        self.stock_items = self.get_GET_items()

        return self.renderJsonResponse(request, self.get_form())

    def post(self, request, *args, **kwargs):

        self.request = request

        self.stock_action = request.POST.get('stock_action', 'invalid').strip().lower()

        # Update list of stock items
        self.stock_items = self.get_POST_items()

        form = self.get_form()

        valid = form.is_valid()
        
        for item in self.stock_items:
            
            try:
                item.new_quantity = Decimal(item.new_quantity)
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

        elif self.stock_action == 'delete':
            return self.do_delete()

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

            item.move(destination, note, self.request.user, quantity=item.new_quantity)

            count += 1

        if count == 0:
            return _('No items were moved')
        
        else:
            return _('Moved {n} items to {dest}'.format(
                n=count,
                dest=destination.pathstring))

    def do_delete(self):
        """ Delete multiple stock items """

        count = 0
        # note = self.request.POST['note']

        for item in self.stock_items:
            
            # TODO - In the future, StockItems should not be 'deleted'
            # TODO - Instead, they should be marked as "inactive"

            item.delete()

            count += 1

        return _("Deleted {n} stock items".format(n=count))


class StockItemEdit(AjaxUpdateView):
    """
    View for editing details of a single StockItem
    """

    model = StockItem
    form_class = StockForms.EditStockItemForm
    context_object_name = 'item'
    ajax_template_name = 'modal_form.html'
    ajax_form_title = _('Edit Stock Item')

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

        if not item.part.trackable or not item.serialized:
            form.fields.pop('serial')

        return form


class StockItemConvert(AjaxUpdateView):
    """
    View for 'converting' a StockItem to a variant of its current part.
    """

    model = StockItem
    form_class = StockForms.ConvertStockItemForm
    ajax_form_title = _('Convert Stock Item')
    ajax_template_name = 'stock/stockitem_convert.html'
    context_object_name = 'item'

    def get_form(self):
        """
        Filter the available parts.
        """

        form = super().get_form()
        item = self.get_object()

        form.fields['part'].queryset = item.part.get_all_variants()

        return form


class StockLocationCreate(AjaxCreateView):
    """
    View for creating a new StockLocation
    A parent location (another StockLocation object) can be passed as a query parameter
    """

    model = StockLocation
    form_class = StockForms.EditStockLocationForm
    context_object_name = 'location'
    ajax_template_name = 'modal_form.html'
    ajax_form_title = _('Create new Stock Location')

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
    ajax_form_title = _('Serialize Stock')
    form_class = StockForms.SerializeStockForm

    def get_form(self):

        context = self.get_form_kwargs()

        # Pass the StockItem object through to the form
        context['item'] = self.get_object()

        form = StockForms.SerializeStockForm(**context)

        return form

    def get_initial(self):

        initials = super().get_initial().copy()

        item = self.get_object()

        initials['quantity'] = item.quantity
        initials['serial_numbers'] = item.part.getSerialNumberString(item.quantity)
        if item.location is not None:
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
                        form.non_field_errors = [messages[k]]

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
    form_class = StockForms.CreateStockItemForm
    context_object_name = 'item'
    ajax_template_name = 'modal_form.html'
    ajax_form_title = _('Create new Stock Item')

    def get_part(self, form=None):
        """
        Attempt to get the "part" associted with this new stockitem.

        - May be passed to the form as a query parameter (e.g. ?part=<id>)
        - May be passed via the form field itself.
        """

        # Try to extract from the URL query
        part_id = self.request.GET.get('part', None)

        if part_id:
            try:
                part = Part.objects.get(pk=part_id)
                return part
            except (Part.DoesNotExist, ValueError):
                pass

        # Try to get from the form
        if form:
            try:
                part_id = form['part'].value()
                part = Part.objects.get(pk=part_id)
                return part
            except (Part.DoesNotExist, ValueError):
                pass

        # Could not extract a part object
        return None

    def get_form(self):
        """ Get form for StockItem creation.
        Overrides the default get_form() method to intelligently limit
        ForeignKey choices based on other selections
        """

        form = super().get_form()

        part = self.get_part(form=form)

        if part is not None:
            sn = part.getNextSerialNumber()
            form.field_placeholder['serial_numbers'] = _('Next available serial number is') + ' ' + str(sn)

            form.rebuild_layout()

            # Hide the 'part' field (as a valid part is selected)
            # form.fields['part'].widget = HiddenInput()

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

        else:
            # No Part has been selected!
            # We must not provide *any* options for SupplierPart
            form.fields['supplier_part'].queryset = SupplierPart.objects.none()

        # Otherwise if the user has selected a SupplierPart, we know what Part they meant!
        if form['supplier_part'].value() is not None:
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
                self.ajax_form_title = _("Duplicate Stock Item")
            except StockItem.DoesNotExist:
                initials = super(StockItemCreate, self).get_initial().copy()

        else:
            initials = super(StockItemCreate, self).get_initial().copy()

        part = self.get_part()

        loc_id = self.request.GET.get('location', None)
        sup_part_id = self.request.GET.get('supplier_part', None)

        location = None
        supplier_part = None

        if part is not None:
            # Check that the supplied part is 'valid'
            if not part.is_template and part.active and not part.virtual:
                initials['part'] = part
                initials['location'] = part.get_default_location()
                initials['supplier_part'] = part.default_supplier

        # SupplierPart field has been specified
        # It must match the Part, if that has been supplied
        if sup_part_id:
            try:
                supplier_part = SupplierPart.objects.get(pk=sup_part_id)

                if part is None or supplier_part.part == part:
                    initials['supplier_part'] = supplier_part

            except (ValueError, SupplierPart.DoesNotExist):
                pass

        # Location has been specified
        if loc_id:
            try:
                location = StockLocation.objects.get(pk=loc_id)
                initials['location'] = location
            except (ValueError, StockLocation.DoesNotExist):
                pass

        return initials

    def post(self, request, *args, **kwargs):
        """ Handle POST of StockItemCreate form.

        - Manage serial-number valdiation for tracked parts
        """

        part = None

        form = self.get_form()

        data = {}

        valid = form.is_valid()

        if valid:
            part_id = form['part'].value()
            try:
                part = Part.objects.get(id=part_id)
                quantity = Decimal(form['quantity'].value())

                sn = part.getNextSerialNumber()
                form.field_placeholder['serial_numbers'] = _("Next available serial number is") + " " + str(sn)

                form.rebuild_layout()

            except (Part.DoesNotExist, ValueError, InvalidOperation):
                part = None
                quantity = 1
                valid = False
                form.errors['quantity'] = [_('Invalid quantity')]

            if quantity < 0:
                form.errors['quantity'] = [_('Quantity cannot be less than zero')]
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
                                if part.checkIfSerialNumberExists(serial):
                                    existing.append(serial)

                            if len(existing) > 0:
                                exists = ",".join([str(x) for x in existing])
                                form.errors['serial_numbers'] = [_('The following serial numbers already exist: ({sn})'.format(sn=exists))]
                                valid = False

                            else:
                                # At this point we have a list of serial numbers which we know are valid,
                                # and do not currently exist
                                form.clean()

                                form_data = form.cleaned_data

                                if form.is_valid():

                                    for serial in serials:
                                        # Create a new stock item for each serial number
                                        item = StockItem(
                                            part=part,
                                            quantity=1,
                                            serial=serial,
                                            supplier_part=form_data.get('supplier_part'),
                                            location=form_data.get('location'),
                                            batch=form_data.get('batch'),
                                            delete_on_deplete=False,
                                            status=form_data.get('status'),
                                            link=form_data.get('link'),
                                        )

                                        item.save(user=request.user)

                                    data['success'] = _('Created {n} new stock items'.format(n=len(serials)))
                                    valid = True

                        except ValidationError as e:
                            form.errors['serial_numbers'] = e.messages
                            valid = False

                    else:
                        # We have a serialized part, but no serial numbers specified...
                        form.clean()
                        form._post_clean()

                        if form.is_valid():

                            item = form.save(commit=False)
                            item.save(user=request.user)

                            data['pk'] = item.pk
                            data['url'] = item.get_absolute_url()
                            data['success'] = _("Created new stock item")

                            valid = True

                else:  # Referenced Part object is not marked as "trackable"
                    # For non-serialized items, simply save the form.
                    # We need to call _post_clean() here because it is prevented in the form implementation
                    form.clean()
                    form._post_clean()

                    if form.is_valid:
                        item = form.save(commit=False)
                        item.save(user=request.user)

                        data['pk'] = item.pk
                        data['url'] = item.get_absolute_url()
                        data['success'] = _("Created new stock item")

                        valid = True

        data['form_valid'] = valid and form.is_valid()

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
    ajax_form_title = _('Delete Stock Location')


class StockItemDelete(AjaxDeleteView):
    """
    View to delete a StockItem
    Presents a deletion confirmation form to the user
    """

    model = StockItem
    success_url = '/stock/'
    ajax_template_name = 'stock/item_delete.html'
    context_object_name = 'item'
    ajax_form_title = _('Delete Stock Item')


class StockItemTrackingDelete(AjaxDeleteView):
    """
    View to delete a StockItemTracking object
    Presents a deletion confirmation form to the user
    """

    model = StockItemTracking
    ajax_template_name = 'stock/tracking_delete.html'
    ajax_form_title = _('Delete Stock Tracking Entry')


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
    ajax_form_title = _('Edit Stock Tracking Entry')
    form_class = StockForms.TrackingEntryForm


class StockItemTrackingCreate(AjaxCreateView):
    """ View for creating a new StockItemTracking object.
    """

    model = StockItemTracking
    ajax_form_title = _("Add Stock Tracking Entry")
    form_class = StockForms.TrackingEntryForm

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
