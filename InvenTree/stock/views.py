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
from django.http import HttpResponseRedirect
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from django.utils.translation import ugettext_lazy as _

from moneyed import CURRENCIES

from InvenTree.views import AjaxView
from InvenTree.views import AjaxUpdateView, AjaxDeleteView, AjaxCreateView
from InvenTree.views import QRCodeView
from InvenTree.views import InvenTreeRoleMixin
from InvenTree.forms import ConfirmForm

from InvenTree.helpers import str2bool, DownloadFile, GetExportFormats
from InvenTree.helpers import extract_serial_numbers

from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta

from company.models import Company, SupplierPart
from part.models import Part
from .models import StockItem, StockLocation, StockItemTracking

import common.settings
from common.models import InvenTreeSetting
from users.models import Owner

from .admin import StockItemResource

from . import forms as StockForms


class StockIndex(InvenTreeRoleMixin, ListView):
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


class StockLocationDetail(InvenTreeRoleMixin, DetailView):
    """
    Detailed view of a single StockLocation object
    """

    context_object_name = 'location'
    template_name = 'stock/location.html'
    queryset = StockLocation.objects.all()
    model = StockLocation


class StockItemDetail(InvenTreeRoleMixin, DetailView):
    """
    Detailed view of a single StockItem object
    """

    context_object_name = 'item'
    template_name = 'stock/item.html'
    queryset = StockItem.objects.all()
    model = StockItem

    def get_context_data(self, **kwargs):
        """ add previous and next item """
        data = super().get_context_data(**kwargs)

        if self.object.serialized:

            serial_elem = {}

            try:
                current = int(self.object.serial)

                for item in self.object.part.stock_items.all():

                    if item.serialized:
                        try:
                            sn = int(item.serial)
                            serial_elem[sn] = item
                        except ValueError:
                            # We only support integer serial number progression
                            pass

                serials = serial_elem.keys()

                # previous
                for nbr in range(current - 1, min(serials), -1):
                    if nbr in serials:
                        data['previous'] = serial_elem.get(nbr, None)
                        break

                # next
                for nbr in range(current + 1, max(serials) + 1):
                    if nbr in serials:
                        data['next'] = serial_elem.get(nbr, None)
                        break

            except ValueError:
                # We only support integer serial number progression
                pass

        return data

    def get(self, request, *args, **kwargs):
        """ check if item exists else return to stock index """

        stock_pk = kwargs.get('pk', None)

        if stock_pk:
            try:
                stock_item = StockItem.objects.get(pk=stock_pk)
            except StockItem.DoesNotExist:
                stock_item = None

            if not stock_item:
                return HttpResponseRedirect(reverse('stock-index'))

        return super().get(request, *args, **kwargs)


class StockLocationEdit(AjaxUpdateView):
    """
    View for editing details of a StockLocation.
    This view is used with the EditStockLocationForm to deliver a modal form to the web view

    TODO: Remove this code as location editing has been migrated to the API forms
          - Have to still validate that all form functionality (as below) as been ported

    """

    model = StockLocation
    form_class = StockForms.EditStockLocationForm
    context_object_name = 'location'
    ajax_template_name = 'modal_form.html'
    ajax_form_title = _('Edit Stock Location')

    def get_form(self):
        """ Customize form data for StockLocation editing.

        Limit the choices for 'parent' field to those which make sense.
        If ownership control is enabled and location has parent, disable owner field.
        """

        form = super(AjaxUpdateView, self).get_form()

        location = self.get_object()

        # Remove any invalid choices for the 'parent' field
        parent_choices = StockLocation.objects.all()
        parent_choices = parent_choices.exclude(id__in=location.getUniqueChildren())

        form.fields['parent'].queryset = parent_choices

        # Is ownership control enabled?
        stock_ownership_control = InvenTreeSetting.get_setting('STOCK_OWNERSHIP_CONTROL')

        if not stock_ownership_control:
            # Hide owner field
            form.fields['owner'].widget = HiddenInput()
        else:
            # Get location's owner
            location_owner = location.owner

            if location_owner:
                if location.parent:
                    try:
                        # If location has parent and owner: automatically select parent's owner
                        parent_owner = location.parent.owner
                        form.fields['owner'].initial = parent_owner
                    except AttributeError:
                        pass
                else:
                    # If current owner exists: automatically select it
                    form.fields['owner'].initial = location_owner

                # Update queryset or disable field (only if not admin)
                if not self.request.user.is_superuser:
                    if type(location_owner.owner) is Group:
                        user_as_owner = Owner.get_owner(self.request.user)
                        queryset = location_owner.get_related_owners(include_group=True)

                        if user_as_owner not in queryset:
                            # Only owners or admin can change current owner
                            form.fields['owner'].disabled = True
                        else:
                            form.fields['owner'].queryset = queryset

        return form

    def save(self, object, form, **kwargs):
        """ If location has children and ownership control is enabled:
            - update owner of all children location of this location
            - update owner for all stock items at this location
        """

        self.object = form.save()

        # Is ownership control enabled?
        stock_ownership_control = InvenTreeSetting.get_setting('STOCK_OWNERSHIP_CONTROL')

        if stock_ownership_control and self.object.owner:
            # Get authorized users
            authorized_owners = self.object.owner.get_related_owners()

            # Update children locations
            children_locations = self.object.get_children()
            for child in children_locations:
                # Check if current owner is subset of new owner
                if child.owner and authorized_owners:
                    if child.owner in authorized_owners:
                        continue

                child.owner = self.object.owner
                child.save()

            # Update stock items
            stock_items = self.object.get_stock_items()

            for stock_item in stock_items:
                # Check if current owner is subset of new owner
                if stock_item.owner and authorized_owners:
                    if stock_item.owner in authorized_owners:
                        continue

                stock_item.owner = self.object.owner
                stock_item.save()

        return self.object

    def validate(self, item, form):
        """ Check that owner is set if stock ownership control is enabled """

        parent = form.cleaned_data.get('parent', None)

        owner = form.cleaned_data.get('owner', None)

        # Is ownership control enabled?
        stock_ownership_control = InvenTreeSetting.get_setting('STOCK_OWNERSHIP_CONTROL')

        if stock_ownership_control:
            if not owner and not self.request.user.is_superuser:
                form.add_error('owner', _('Owner is required (ownership control is enabled)'))
            else:
                try:
                    if parent.owner:
                        if parent.owner != owner:
                            error = f'Owner requires to be equivalent to parent\'s owner ({parent.owner})'
                            form.add_error('owner', error)
                except AttributeError:
                    # No parent
                    pass


class StockLocationQRCode(QRCodeView):
    """ View for displaying a QR code for a StockLocation object """

    ajax_form_title = _("Stock Location QR code")

    role_required = ['stock_location.view', 'stock.view']

    def get_qr_data(self):
        """ Generate QR code data for the StockLocation """
        try:
            loc = StockLocation.objects.get(id=self.pk)
            return loc.format_barcode()
        except StockLocation.DoesNotExist:
            return None


class StockItemAssignToCustomer(AjaxUpdateView):
    """
    View for manually assigning a StockItem to a Customer
    """

    model = StockItem
    ajax_form_title = _("Assign to Customer")
    context_object_name = "item"
    form_class = StockForms.AssignStockItemToCustomerForm

    def validate(self, item, form, **kwargs):

        customer = form.cleaned_data.get('customer', None)

        if not customer:
            form.add_error('customer', _('Customer must be specified'))

    def save(self, item, form, **kwargs):
        """
        Assign the stock item to the customer.
        """

        customer = form.cleaned_data.get('customer', None)

        if customer:
            item = item.allocateToCustomer(
                customer,
                user=self.request.user
            )

            item.clearAllocations()


class StockItemReturnToStock(AjaxUpdateView):
    """
    View for returning a stock item (which is assigned to a customer) to stock.
    """

    model = StockItem
    ajax_form_title = _("Return to Stock")
    context_object_name = "item"
    form_class = StockForms.ReturnStockItemForm

    def validate(self, item, form, **kwargs):

        location = form.cleaned_data.get('location', None)

        if not location:
            form.add_error('location', _('Specify a valid location'))

    def save(self, item, form, **kwargs):

        location = form.cleaned_data.get('location', None)

        if location:
            item.returnFromCustomer(location, self.request.user)

    def get_data(self):
        return {
            'success': _('Stock item returned from customer')
        }


class StockItemDeleteTestData(AjaxUpdateView):
    """
    View for deleting all test data
    """

    model = StockItem
    form_class = ConfirmForm
    ajax_form_title = _("Delete All Test Data")

    role_required = ['stock.change', 'stock.delete']

    def get_form(self):
        return ConfirmForm()

    def post(self, request, *args, **kwargs):

        valid = False

        stock_item = StockItem.objects.get(pk=self.kwargs['pk'])
        form = self.get_form()

        confirm = str2bool(request.POST.get('confirm', False))

        if confirm is not True:
            form.add_error('confirm', _('Confirm test data deletion'))
            form.add_error(None, _('Check the confirmation box'))
        else:
            stock_item.test_results.all().delete()
            valid = True

        data = {
            'form_valid': valid,
        }

        return self.renderJsonResponse(request, form, data)


class StockExport(AjaxView):
    """ Export stock data from a particular location.
    Returns a file containing stock information for that location.
    """

    model = StockItem
    role_required = 'stock.view'

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
            # Check if locations should be cascading
            cascade = str2bool(request.GET.get('cascade', True))
            stock_items = location.get_stock_items(cascade)
        else:
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
    role_required = 'stock.view'

    def get_qr_data(self):
        """ Generate QR code data for the StockItem """
        try:
            item = StockItem.objects.get(id=self.pk)
            return item.format_barcode()
        except StockItem.DoesNotExist:
            return None


class StockItemInstall(AjaxUpdateView):
    """
    View for manually installing stock items into
    a particular stock item.

    In contrast to the StockItemUninstall view,
    only a single stock item can be installed at once.

    The "part" to be installed must be provided in the GET query parameters.

    """

    model = StockItem
    form_class = StockForms.InstallStockForm
    ajax_form_title = _('Install Stock Item')
    ajax_template_name = "stock/item_install.html"

    part = None

    def get_params(self):
        """ Retrieve GET parameters """

        # Look at GET params
        self.part_id = self.request.GET.get('part', None)
        self.install_in = self.request.GET.get('install_in', False)
        self.install_item = self.request.GET.get('install_item', False)

        if self.part_id is None:
            # Look at POST params
            self.part_id = self.request.POST.get('part', None)

        try:
            self.part = Part.objects.get(pk=self.part_id)
        except (ValueError, Part.DoesNotExist):
            self.part = None

    def get_stock_items(self):
        """
        Return a list of stock items suitable for displaying to the user.

        Requirements:
        - Items must be in stock
        - Items must be in BOM of stock item
        - Items must be serialized
        """
        
        # Filter items in stock
        items = StockItem.objects.filter(StockItem.IN_STOCK_FILTER)

        # Filter serialized stock items
        items = items.exclude(serial__isnull=True).exclude(serial__exact='')

        if self.part:
            # Filter for parts to install this item in
            if self.install_in:
                # Get parts using this part
                allowed_parts = self.part.get_used_in()
                # Filter
                items = items.filter(part__in=allowed_parts)

            # Filter for parts to install in this item
            if self.install_item:
                # Get parts used in this part's BOM
                bom_items = self.part.get_bom_items()
                allowed_parts = [item.sub_part for item in bom_items]
                # Filter
                items = items.filter(part__in=allowed_parts)

        return items

    def get_context_data(self, **kwargs):
        """ Retrieve parameters and update context """

        ctx = super().get_context_data(**kwargs)

        # Get request parameters
        self.get_params()

        ctx.update({
            'part': self.part,
            'install_in': self.install_in,
            'install_item': self.install_item,
        })

        return ctx

    def get_initial(self):

        initials = super().get_initial()

        items = self.get_stock_items()

        # If there is a single stock item available, we can use it!
        if items.count() == 1:
            item = items.first()
            initials['stock_item'] = item.pk

        if self.part:
            initials['part'] = self.part

        try:
            # Is this stock item being installed in the other stock item?
            initials['to_install'] = self.install_in or not self.install_item
        except AttributeError:
            pass

        return initials

    def get_form(self):

        form = super().get_form()

        form.fields['stock_item'].queryset = self.get_stock_items()

        return form

    def post(self, request, *args, **kwargs):

        self.get_params()

        form = self.get_form()

        valid = form.is_valid()

        if valid:
            # We assume by this point that we have a valid stock_item and quantity values
            data = form.cleaned_data

            other_stock_item = data['stock_item']
            # Quantity will always be 1 for serialized item
            quantity = 1
            notes = data['notes']

            # Get stock item
            this_stock_item = self.get_object()

            if data['to_install']:
                # Install this stock item into the other stock item
                other_stock_item.installStockItem(this_stock_item, quantity, request.user, notes)
            else:
                # Install the other stock item into this one
                this_stock_item.installStockItem(other_stock_item, quantity, request.user, notes)

        data = {
            'form_valid': valid,
        }

        return self.renderJsonResponse(request, form, data=data)


class StockItemUninstall(AjaxView, FormMixin):
    """
    View for uninstalling one or more StockItems,
    which are installed in another stock item.

    Stock items are uninstalled into a location,
    defaulting to the location that they were "in" before they were installed.

    If multiple default locations are detected,
    leave the final location up to the user.
    """

    ajax_template_name = 'stock/stock_uninstall.html'
    ajax_form_title = _('Uninstall Stock Items')
    form_class = StockForms.UninstallStockForm
    role_required = 'stock.change'

    # List of stock items to uninstall (initially empty)
    stock_items = []

    def get_stock_items(self):

        return self.stock_items

    def get_initial(self):

        initials = super().get_initial().copy()

        # Keep track of the current locations of stock items
        current_locations = set()

        # Keep track of the default locations for stock items
        default_locations = set()

        for item in self.stock_items:

            if item.location:
                current_locations.add(item.location)

            if item.part.default_location:
                default_locations.add(item.part.default_location)

        if len(current_locations) == 1:
            # If the selected stock items are currently in a single location,
            # select that location as the destination.
            initials['location'] = next(iter(current_locations))
        elif len(current_locations) == 0:
            # There are no current locations set
            if len(default_locations) == 1:
                # Select the single default location
                initials['location'] = next(iter(default_locations))

        return initials

    def get(self, request, *args, **kwargs):

        """ Extract list of stock items, which are supplied as a list,
        e.g. items[]=1,2,3
        """

        if 'items[]' in request.GET:
            self.stock_items = StockItem.objects.filter(id__in=request.GET.getlist('items[]'))
        else:
            self.stock_items = []

        return self.renderJsonResponse(request, self.get_form())

    def post(self, request, *args, **kwargs):

        """
        Extract a list of stock items which are included as hidden inputs in the form data.
        """

        items = []

        for item in self.request.POST:
            if item.startswith('stock-item-'):
                pk = item.replace('stock-item-', '')

                try:
                    stock_item = StockItem.objects.get(pk=pk)
                    items.append(stock_item)
                except (ValueError, StockItem.DoesNotExist):
                    pass

        self.stock_items = items

        # Assume the form is valid, until it isn't!
        valid = True

        confirmed = str2bool(request.POST.get('confirm'))

        note = request.POST.get('note', '')

        location = request.POST.get('location', None)

        if location:
            try:
                location = StockLocation.objects.get(pk=location)
            except (ValueError, StockLocation.DoesNotExist):
                location = None

        if not location:
            # Location is required!
            valid = False

        form = self.get_form()

        if not confirmed:
            valid = False
            form.add_error('confirm', _('Confirm stock adjustment'))

        data = {
            'form_valid': valid,
        }

        if valid:
            # Ok, now let's actually uninstall the stock items
            for item in self.stock_items:
                item.uninstallIntoLocation(location, request.user, note)

            data['success'] = _('Uninstalled stock items')

        return self.renderJsonResponse(request, form=form, data=data)

    def get_context_data(self):

        context = super().get_context_data()

        context['stock_items'] = self.get_stock_items()

        return context


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

        # Hide the "expiry date" field if the feature is not enabled
        if not common.settings.stock_expiry_enabled():
            form.fields['expiry_date'].widget = HiddenInput()

        item = self.get_object()

        # If the part cannot be purchased, hide the supplier_part field
        if not item.part.purchaseable:
            form.fields['supplier_part'].widget = HiddenInput()

            form.fields.pop('purchase_price')
        else:
            query = form.fields['supplier_part'].queryset
            query = query.filter(part=item.part.id)
            form.fields['supplier_part'].queryset = query

        # Hide the serial number field if it is not required
        if not item.part.trackable and not item.serialized:
            form.fields['serial'].widget = HiddenInput()

        location = item.location

        # Is ownership control enabled?
        stock_ownership_control = InvenTreeSetting.get_setting('STOCK_OWNERSHIP_CONTROL')

        if not stock_ownership_control:
            form.fields['owner'].widget = HiddenInput()
        else:
            try:
                location_owner = location.owner
            except AttributeError:
                location_owner = None

            # Check if location has owner
            if location_owner:
                form.fields['owner'].initial = location_owner

                # Check location's owner type and filter potential owners
                if type(location_owner.owner) is Group:
                    user_as_owner = Owner.get_owner(self.request.user)
                    queryset = location_owner.get_related_owners(include_group=True)

                    if user_as_owner in queryset:
                        form.fields['owner'].initial = user_as_owner

                    form.fields['owner'].queryset = queryset

                elif type(location_owner.owner) is get_user_model():
                    # If location's owner is a user: automatically set owner field and disable it
                    form.fields['owner'].disabled = True
                    form.fields['owner'].initial = location_owner

            try:
                item_owner = item.owner
            except AttributeError:
                item_owner = None

            # Check if item has owner
            if item_owner:
                form.fields['owner'].initial = item_owner

                # Check item's owner type and filter potential owners
                if type(item_owner.owner) is Group:
                    user_as_owner = Owner.get_owner(self.request.user)
                    queryset = item_owner.get_related_owners(include_group=True)

                    if user_as_owner in queryset:
                        form.fields['owner'].initial = user_as_owner

                    form.fields['owner'].queryset = queryset

                elif type(item_owner.owner) is get_user_model():
                    # If item's owner is a user: automatically set owner field and disable it
                    form.fields['owner'].disabled = True
                    form.fields['owner'].initial = item_owner

        return form

    def validate(self, item, form):
        """ Check that owner is set if stock ownership control is enabled """

        owner = form.cleaned_data.get('owner', None)

        # Is ownership control enabled?
        stock_ownership_control = InvenTreeSetting.get_setting('STOCK_OWNERSHIP_CONTROL')

        if stock_ownership_control:
            if not owner and not self.request.user.is_superuser:
                form.add_error('owner', _('Owner is required (ownership control is enabled)'))

    def save(self, object, form, **kwargs):
        """
        Override the save method, to track the user who updated the model
        """

        item = form.save(commit=False)

        item.save(user=self.request.user)

        return item
        

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

        form.fields['part'].queryset = item.part.get_conversion_options()

        return form


class StockLocationCreate(AjaxCreateView):
    """
    View for creating a new StockLocation
    A parent location (another StockLocation object) can be passed as a query parameter

    TODO: Remove this class entirely, as it has been migrated to the API forms
          - Still need to check that all the functionality (as below) has been implemented

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

    def get_form(self):
        """ Disable owner field when:
            - creating child location
            - and stock ownership control is enable
        """

        form = super().get_form()

        # Is ownership control enabled?
        stock_ownership_control = InvenTreeSetting.get_setting('STOCK_OWNERSHIP_CONTROL')

        if not stock_ownership_control:
            # Hide owner field
            form.fields['owner'].widget = HiddenInput()
        else:
            # If user did not selected owner: automatically match to parent's owner
            if not form['owner'].data:
                try:
                    parent_id = form['parent'].value()
                    parent = StockLocation.objects.get(pk=parent_id)

                    if parent:
                        form.fields['owner'].initial = parent.owner
                        if not self.request.user.is_superuser:
                            form.fields['owner'].disabled = True
                except StockLocation.DoesNotExist:
                    pass
                except ValueError:
                    pass

        return form

    def save(self, form):
        """ If parent location exists then use it to set the owner """

        self.object = form.save(commit=False)

        parent = form.cleaned_data.get('parent', None)

        if parent:
            # Select parent's owner
            self.object.owner = parent.owner

        self.object.save()

        return self.object

    def validate(self, item, form):
        """ Check that owner is set if stock ownership control is enabled """

        parent = form.cleaned_data.get('parent', None)

        owner = form.cleaned_data.get('owner', None)

        # Is ownership control enabled?
        stock_ownership_control = InvenTreeSetting.get_setting('STOCK_OWNERSHIP_CONTROL')

        if stock_ownership_control:
            if not owner and not self.request.user.is_superuser:
                form.add_error('owner', _('Owner is required (ownership control is enabled)'))
            else:
                try:
                    if parent.owner:
                        if parent.owner != owner:
                            error = f'Owner requires to be equivalent to parent\'s owner ({parent.owner})'
                            form.add_error('owner', error)
                except AttributeError:
                    # No parent
                    pass


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

        # Hide the "expiry date" field if the feature is not enabled
        if not common.settings.stock_expiry_enabled():
            form.fields['expiry_date'].widget = HiddenInput()

        part = self.get_part(form=form)

        if part is not None:

            # Add placeholder text for the serial number field
            form.field_placeholder['serial_numbers'] = part.getSerialNumberString()

            form.rebuild_layout()

            if not part.purchaseable:
                form.fields.pop('purchase_price')

            # Hide the 'part' field (as a valid part is selected)
            # form.fields['part'].widget = HiddenInput()

            # Trackable parts get special consideration:
            if part.trackable:
                form.fields['delete_on_deplete'].disabled = True
            else:
                form.fields['serial_numbers'].disabled = True

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

            form.fields['serial_numbers'].disabled = True

        # Otherwise if the user has selected a SupplierPart, we know what Part they meant!
        if form['supplier_part'].value() is not None:
            pass

        location = None
        try:
            loc_id = form['location'].value()
            location = StockLocation.objects.get(pk=loc_id)
        except StockLocation.DoesNotExist:
            pass
        except ValueError:
            pass

        # Is ownership control enabled?
        stock_ownership_control = InvenTreeSetting.get_setting('STOCK_OWNERSHIP_CONTROL')
        if not stock_ownership_control:
            form.fields['owner'].widget = HiddenInput()
        else:
            try:
                location_owner = location.owner
            except AttributeError:
                location_owner = None

            if location_owner:
                # Check location's owner type and filter potential owners
                if type(location_owner.owner) is Group:
                    user_as_owner = Owner.get_owner(self.request.user)
                    queryset = location_owner.get_related_owners()

                    if user_as_owner in queryset:
                        form.fields['owner'].initial = user_as_owner

                    form.fields['owner'].queryset = queryset

                elif type(location_owner.owner) is get_user_model():
                    # If location's owner is a user: automatically set owner field and disable it
                    form.fields['owner'].disabled = True
                    form.fields['owner'].initial = location_owner

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
            initials['part'] = part
            initials['location'] = part.get_default_location()
            initials['supplier_part'] = part.default_supplier

            # If the part has a defined expiry period, extrapolate!
            if part.default_expiry > 0:
                expiry_date = datetime.now().date() + timedelta(days=part.default_expiry)
                initials['expiry_date'] = expiry_date

        currency_code = common.settings.currency_code_default()

        # SupplierPart field has been specified
        # It must match the Part, if that has been supplied
        if sup_part_id:
            try:
                supplier_part = SupplierPart.objects.get(pk=sup_part_id)

                if part is None or supplier_part.part == part:
                    initials['supplier_part'] = supplier_part

                    currency_code = supplier_part.supplier.currency_code

            except (ValueError, SupplierPart.DoesNotExist):
                pass

        # Location has been specified
        if loc_id:
            try:
                location = StockLocation.objects.get(pk=loc_id)
                initials['location'] = location
            except (ValueError, StockLocation.DoesNotExist):
                pass

        currency = CURRENCIES.get(currency_code, None)

        if currency:
            initials['purchase_price'] = (None, currency)

        return initials

    def validate(self, item, form):
        """
        Extra form validation steps
        """

        data = form.cleaned_data

        part = data.get('part', None)

        quantity = data.get('quantity', None)

        owner = data.get('owner', None)

        if not part:
            return

        if not quantity:
            return

        try:
            quantity = Decimal(quantity)
        except (ValueError, InvalidOperation):
            form.add_error('quantity', _('Invalid quantity provided'))
            return

        if quantity < 0:
            form.add_error('quantity', _('Quantity cannot be negative'))

        # Trackable parts are treated differently
        if part.trackable:
            sn = data.get('serial_numbers', '')
            sn = str(sn).strip()

            if len(sn) > 0:
                try:
                    serials = extract_serial_numbers(sn, quantity)
                except ValidationError as e:
                    serials = None
                    form.add_error('serial_numbers', e.messages)

                if serials is not None:
                    existing = part.find_conflicting_serial_numbers(serials)

                    if len(existing) > 0:
                        exists = ','.join([str(x) for x in existing])

                        form.add_error(
                            'serial_numbers',
                            _('Serial numbers already exist') + ': ' + exists
                        )

        # Is ownership control enabled?
        stock_ownership_control = InvenTreeSetting.get_setting('STOCK_OWNERSHIP_CONTROL')

        if stock_ownership_control:
            # Check if owner is set
            if not owner and not self.request.user.is_superuser:
                form.add_error('owner', _('Owner is required (ownership control is enabled)'))
                return

    def save(self, form, **kwargs):
        """
        Create a new StockItem based on the provided form data.
        """

        data = form.cleaned_data

        part = data['part']

        quantity = data['quantity']

        if part.trackable:
            sn = data.get('serial_numbers', '')
            sn = str(sn).strip()

            # Create a single stock item for each provided serial number
            if len(sn) > 0:
                serials = extract_serial_numbers(sn, quantity)

                for serial in serials:
                    item = StockItem(
                        part=part,
                        quantity=1,
                        serial=serial,
                        supplier_part=data.get('supplier_part', None),
                        location=data.get('location', None),
                        batch=data.get('batch', None),
                        delete_on_deplete=False,
                        status=data.get('status'),
                        link=data.get('link', ''),
                    )

                    item.save(user=self.request.user)

            # Create a single StockItem of the specified quantity
            else:
                form._post_clean()

                item = form.save(commit=False)
                item.user = self.request.user
                item.save(user=self.request.user)

                return item

        # Non-trackable part
        else:

            form._post_clean()

            item = form.save(commit=False)
            item.user = self.request.user
            item.save(user=self.request.user)

            return item


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
