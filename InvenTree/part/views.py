"""
Django views for interacting with Part app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import get_object_or_404

from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView
from django.forms.models import model_to_dict
from django.forms import HiddenInput, CheckboxInput

from company.models import Company
from .models import PartCategory, Part, PartAttachment
from .models import BomItem
from .models import SupplierPart
from .models import match_part_names

from . import forms as part_forms

from InvenTree.views import AjaxView, AjaxCreateView, AjaxUpdateView, AjaxDeleteView
from InvenTree.views import QRCodeView

from InvenTree.helpers import DownloadFile, str2bool


class PartIndex(ListView):
    """ View for displaying list of Part objects
    """
    model = Part
    template_name = 'part/category.html'
    context_object_name = 'parts'

    def get_queryset(self):
        return Part.objects.all()  # filter(category=None)

    def get_context_data(self, **kwargs):

        context = super(PartIndex, self).get_context_data(**kwargs).copy()

        # View top-level categories
        children = PartCategory.objects.filter(parent=None)

        context['children'] = children

        return context


class PartAttachmentCreate(AjaxCreateView):
    """ View for creating a new PartAttachment object

    - The view only makes sense if a Part object is passed to it
    """
    model = PartAttachment
    form_class = part_forms.EditPartAttachmentForm
    ajax_form_title = "Add part attachment"
    ajax_template_name = "modal_form.html"

    def get_data(self):
        return {
            'success': 'Added attachment'
        }

    def get_initial(self):
        """ Get initial data for new PartAttachment object.

        - Client should have requested this form with a parent part in mind
        - e.g. ?part=<pk>
        """

        initials = super(AjaxCreateView, self).get_initial()

        # TODO - If the proper part was not sent, return an error message
        initials['part'] = Part.objects.get(id=self.request.GET.get('part'))

        return initials

    def get_form(self):
        """ Create a form to upload a new PartAttachment

        - Hide the 'part' field
        """

        form = super(AjaxCreateView, self).get_form()

        form.fields['part'].widget = HiddenInput()

        return form


class PartAttachmentEdit(AjaxUpdateView):
    """ View for editing a PartAttachment object """
    model = PartAttachment
    form_class = part_forms.EditPartAttachmentForm
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Edit attachment'
    
    def get_data(self):
        return {
            'success': 'Part attachment updated'
        }

    def get_form(self):
        form = super(AjaxUpdateView, self).get_form()

        form.fields['part'].widget = HiddenInput()

        return form


class PartAttachmentDelete(AjaxDeleteView):
    """ View for deleting a PartAttachment """

    model = PartAttachment
    ajax_form_title = "Delete Part Attachment"
    ajax_template_name = "part/attachment_delete.html"
    context_object_name = "attachment"

    def get_data(self):
        return {
            'danger': 'Deleted part attachment'
        }


class PartDuplicate(AjaxCreateView):
    """ View for duplicating an existing Part object.

    - Part <pk> is provided in the URL '/part/<pk>/copy/'
    - Option for 'deep-copy' which will duplicate all BOM items (default = True)
    """

    model = Part
    form_class = part_forms.EditPartForm

    ajax_form_title = "Duplicate Part"
    ajax_template_name = "part/copy_part.html"

    def get_data(self):
        return {
            'success': 'Copied part'
        }

    def get_part_to_copy(self):
        try:
            return Part.objects.get(id=self.kwargs['pk'])
        except Part.DoesNotExist:
            return None

    def get_context_data(self):
        return {
            'part': self.get_part_to_copy()
        }

    def get_form(self):
        form = super(AjaxCreateView, self).get_form()

        # Force display of the 'deep_copy' widget
        form.fields['deep_copy'].widget = CheckboxInput()

        return form

    def post(self, request, *args, **kwargs):
        """ Capture the POST request for part duplication

        - If the deep_copy object is set, copy all the BOM items too!
        """

        form = self.get_form()

        context = self.get_context_data()

        valid = form.is_valid()

        name = request.POST.get('name', None)
        
        if name:
            matches = match_part_names(name)

            if len(matches) > 0:
                context['matches'] = matches
            
                # Enforce display of the checkbox
                form.fields['confirm_creation'].widget = CheckboxInput()
                
                # Check if the user has checked the 'confirm_creation' input
                confirmed = str2bool(request.POST.get('confirm_creation', False))

                if not confirmed:
                    form.errors['confirm_creation'] = ['Possible matches exist - confirm creation of new part']
                    
                    form.pre_form_warning = 'Possible matches exist - confirm creation of new part'
                    valid = False

        data = {
            'form_valid': valid
        }

        if valid:
            # Create the new Part
            part = form.save()

            data['pk'] = part.pk

            deep_copy = str2bool(request.POST.get('deep_copy', False))

            original = self.get_part_to_copy()

            if original:
                    part.deepCopy(original, bom=deep_copy)

            try:
                data['url'] = part.get_absolute_url()
            except AttributeError:
                pass

        if valid:
            pass

        return self.renderJsonResponse(request, form, data, context=context)

    def get_initial(self):
        """ Get initial data based on the Part to be copied from.
        """

        part = self.get_part_to_copy()

        if part:
            initials = model_to_dict(part)
        else:
            initials = super(AjaxCreateView, self).get_initial()

        return initials


class PartCreate(AjaxCreateView):
    """ View for creating a new Part object.

    Options for providing initial conditions:
    
    - Provide a category object as initial data
    """
    model = Part
    form_class = part_forms.EditPartForm

    ajax_form_title = 'Create new part'
    ajax_template_name = 'part/create_part.html'

    def get_data(self):
        return {
            'success': "Created new part",
        }

    def get_category_id(self):
        return self.request.GET.get('category', None)

    def get_context_data(self, **kwargs):
        """ Provide extra context information for the form to display:

        - Add category information (if provided)
        """
        context = super(PartCreate, self).get_context_data(**kwargs)

        # Add category information to the page
        cat_id = self.get_category_id()

        if cat_id:
            try:
                context['category'] = PartCategory.objects.get(pk=cat_id)
            except PartCategory.DoesNotExist:
                pass

        return context

    def get_form(self):
        """ Create Form for making new Part object.
        Remove the 'default_supplier' field as there are not yet any matching SupplierPart objects
        """
        form = super(AjaxCreateView, self).get_form()

        # Hide the default_supplier field (there are no matching supplier parts yet!)
        form.fields['default_supplier'].widget = HiddenInput()

        return form

    def post(self, request, *args, **kwargs):

        form = self.get_form()

        context = {}

        valid = form.is_valid()
        
        name = request.POST.get('name', None)
        
        if name:
            matches = match_part_names(name)

            if len(matches) > 0:
                context['matches'] = matches
            
                # Enforce display of the checkbox
                form.fields['confirm_creation'].widget = CheckboxInput()
                
                # Check if the user has checked the 'confirm_creation' input
                confirmed = str2bool(request.POST.get('confirm_creation', False))

                if not confirmed:
                    form.errors['confirm_creation'] = ['Possible matches exist - confirm creation of new part']
                    
                    form.pre_form_warning = 'Possible matches exist - confirm creation of new part'
                    valid = False

        data = {
            'form_valid': valid
        }

        if valid:
            # Create the new Part
            part = form.save()

            data['pk'] = part.pk

            try:
                data['url'] = part.get_absolute_url()
            except AttributeError:
                pass

        return self.renderJsonResponse(request, form, data, context=context)

    def get_initial(self):
        """ Get initial data for the new Part object:

        - If a category is provided, pre-fill the Category field
        """

        initials = super(PartCreate, self).get_initial()

        if self.get_category_id():
            try:
                initials['category'] = PartCategory.objects.get(pk=self.get_category_id())
            except PartCategory.DoesNotExist:
                pass

        return initials


class PartDetail(DetailView):
    """ Detail view for Part object
    """

    context_object_name = 'part'
    queryset = Part.objects.all()
    template_name = 'part/detail.html'

    # Add in some extra context information based on query params
    def get_context_data(self, **kwargs):
        """ Provide extra context data to template

        - If '?editing=True', set 'editing_enabled' context variable
        """
        context = super(PartDetail, self).get_context_data(**kwargs)

        if str2bool(self.request.GET.get('edit', '')):
            context['editing_enabled'] = 1
        else:
            context['editing_enabled'] = 0

        part = self.get_object()

        context['starred'] = part.isStarredBy(self.request.user)

        return context


class PartQRCode(QRCodeView):
    """ View for displaying a QR code for a Part object """

    ajax_form_title = "Part QR Code"

    def get_qr_data(self):
        """ Generate QR code data for the Part """

        try:
            part = Part.objects.get(id=self.pk)
            return part.format_barcode()
        except Part.DoesNotExist:
            return None


class PartImage(AjaxUpdateView):
    """ View for uploading Part image """

    model = Part
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Upload Part Image'
    form_class = part_forms.PartImageForm

    def get_data(self):
        return {
            'success': 'Updated part image',
        }


class PartEdit(AjaxUpdateView):
    """ View for editing Part object """

    model = Part
    form_class = part_forms.EditPartForm
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Edit Part Properties'
    context_object_name = 'part'

    def get_form(self):
        """ Create form for Part editing.
        Overrides default get_form() method to limit the choices
        for the 'default_supplier' field to SupplierParts that reference this part
        """

        form = super(AjaxUpdateView, self).get_form()

        part = self.get_object()

        form.fields['default_supplier'].queryset = SupplierPart.objects.filter(part=part)

        return form


class BomValidate(AjaxUpdateView):
    """ Modal form view for validating a part BOM """

    model = Part
    ajax_form_title = "Validate BOM"
    ajax_template_name = 'part/bom_validate.html'
    context_object_name = 'part'
    form_class = part_forms.BomValidateForm

    def get_context(self):
        return {
            'part': self.get_object(),
        }

    def get(self, request, *args, **kwargs):

        form = self.get_form()

        return self.renderJsonResponse(request, form, context=self.get_context())

    def post(self, request, *args, **kwargs):

        form = self.get_form()
        part = self.get_object()

        confirmed = str2bool(request.POST.get('validate', False))

        if confirmed:
            part.validate_bom(request.user)
        else:
            form.errors['validate'] = ['Confirm that the BOM is valid']

        data = {
            'form_valid': confirmed
        }

        return self.renderJsonResponse(request, form, data, context=self.get_context())


class BomExport(AjaxView):

    model = Part
    ajax_form_title = 'Export BOM'
    ajax_template_name = 'part/bom_export.html'
    form_class = part_forms.BomExportForm

    def get_object(self):
        return get_object_or_404(Part, pk=self.kwargs['pk'])

    def get(self, request, *args, **kwargs):
        form = self.form_class()

        return self.renderJsonResponse(request, form)

    def post(self, request, *args, **kwargs):
        """
        User has now submitted the BOM export data
        """

        # part = self.get_object()

        return super(AjaxView, self).post(request, *args, **kwargs)

    def get_data(self):
        return {
            # 'form_valid': True,
            # 'redirect': '/'
            # 'redirect': reverse('bom-download', kwargs={'pk': self.request.GET.get('pk')})
        }


class BomDownload(AjaxView):
    """
    Provide raw download of a BOM file.
    - File format should be passed as a query param e.g. ?format=csv
    """

    # TODO - This should no longer extend an AjaxView!

    model = Part
    # form_class = BomExportForm
    # template_name = 'part/bom_export.html'
    # ajax_form_title = 'Export Bill of Materials'
    # context_object_name = 'part'

    def get(self, request, *args, **kwargs):

        part = get_object_or_404(Part, pk=self.kwargs['pk'])

        export_format = request.GET.get('format', 'csv')

        # Placeholder to test file export
        filename = '"' + part.name + '_BOM.' + export_format + '"'

        filedata = part.export_bom(format=export_format)

        return DownloadFile(filedata, filename)

    def get_data(self):
        return {
            'info': 'Exported BOM'
        }


class PartDelete(AjaxDeleteView):
    """ View to delete a Part object """

    model = Part
    ajax_template_name = 'part/partial_delete.html'
    ajax_form_title = 'Confirm Part Deletion'
    context_object_name = 'part'

    success_url = '/part/'

    def get_data(self):
        return {
            'danger': 'Part was deleted',
        }


class CategoryDetail(DetailView):
    """ Detail view for PartCategory """
    model = PartCategory
    context_object_name = 'category'
    queryset = PartCategory.objects.all()
    template_name = 'part/category.html'


class CategoryEdit(AjaxUpdateView):
    """ Update view to edit a PartCategory """
    model = PartCategory
    form_class = part_forms.EditCategoryForm
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Edit Part Category'

    def get_context_data(self, **kwargs):
        context = super(CategoryEdit, self).get_context_data(**kwargs).copy()

        try:
            context['category'] = self.get_object()
        except:
            pass

        return context

    def get_form(self):
        """ Customize form data for PartCategory editing.

        Limit the choices for 'parent' field to those which make sense
        """
        
        form = super(AjaxUpdateView, self).get_form()
        
        category = self.get_object()

        # Remove any invalid choices for the parent category part
        parent_choices = PartCategory.objects.all()
        parent_choices = parent_choices.exclude(id__in=category.getUniqueChildren())

        form.fields['parent'].queryset = parent_choices

        return form


class CategoryDelete(AjaxDeleteView):
    """ Delete view to delete a PartCategory """
    model = PartCategory
    ajax_template_name = 'part/category_delete.html'
    ajax_form_title = 'Delete Part Category'
    context_object_name = 'category'
    success_url = '/part/'

    def get_data(self):
        return {
            'danger': 'Part category was deleted',
        }


class CategoryCreate(AjaxCreateView):
    """ Create view to make a new PartCategory """
    model = PartCategory
    ajax_form_action = reverse_lazy('category-create')
    ajax_form_title = 'Create new part category'
    ajax_template_name = 'modal_form.html'
    form_class = part_forms.EditCategoryForm

    def get_context_data(self, **kwargs):
        """ Add extra context data to template.

        - If parent category provided, pass the category details to the template
        """
        context = super(CategoryCreate, self).get_context_data(**kwargs).copy()

        parent_id = self.request.GET.get('category', None)

        if parent_id:
            try:
                context['category'] = PartCategory.objects.get(pk=parent_id)
            except PartCategory.DoesNotExist:
                pass

        return context

    def get_initial(self):
        """ Get initial data for new PartCategory

        - If parent provided, pre-fill the parent category
        """
        initials = super(CategoryCreate, self).get_initial().copy()

        parent_id = self.request.GET.get('category', None)

        if parent_id:
            try:
                initials['parent'] = PartCategory.objects.get(pk=parent_id)
            except PartCategory.DoesNotExist:
                pass

        return initials


class BomItemDetail(DetailView):
    """ Detail view for BomItem """
    context_object_name = 'item'
    queryset = BomItem.objects.all()
    template_name = 'part/bom-detail.html'


class BomItemCreate(AjaxCreateView):
    """ Create view for making a new BomItem object """
    model = BomItem
    form_class = part_forms.EditBomItemForm
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Create BOM item'

    def get_form(self):
        """ Override get_form() method to reduce Part selection options.

        - Do not allow part to be added to its own BOM
        - Remove any Part items that are already in the BOM
        """

        form = super(AjaxCreateView, self).get_form()

        part_id = form['part'].value()

        try:
            part = Part.objects.get(id=part_id)

            # Don't allow selection of sub_part objects which are already added to the Bom!
            query = form.fields['sub_part'].queryset
            
            # Don't allow a part to be added to its own BOM
            query = query.exclude(id=part.id)
            
            # Eliminate any options that are already in the BOM!
            query = query.exclude(id__in=[item.id for item in part.required_parts()])
            
            form.fields['sub_part'].queryset = query
        except Part.DoesNotExist:
            pass

        return form

    def get_initial(self):
        """ Provide initial data for the BomItem:

        - If 'parent' provided, set the parent part field
        """

        # Look for initial values
        initials = super(BomItemCreate, self).get_initial().copy()

        # Parent part for this item?
        parent_id = self.request.GET.get('parent', None)

        if parent_id:
            try:
                initials['part'] = Part.objects.get(pk=parent_id)
            except Part.DoesNotExist:
                pass

        return initials


class BomItemEdit(AjaxUpdateView):
    """ Update view for editing BomItem """

    model = BomItem
    form_class = part_forms.EditBomItemForm
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Edit BOM item'


class BomItemDelete(AjaxDeleteView):
    """ Delete view for removing BomItem """
    model = BomItem
    ajax_template_name = 'part/bom-delete.html'
    context_object_name = 'item'
    ajax_form_title = 'Confim BOM item deletion'


class SupplierPartDetail(DetailView):
    """ Detail view for SupplierPart """
    model = SupplierPart
    template_name = 'company/partdetail.html'
    context_object_name = 'part'
    queryset = SupplierPart.objects.all()


class SupplierPartEdit(AjaxUpdateView):
    """ Update view for editing SupplierPart """

    model = SupplierPart
    context_object_name = 'part'
    form_class = part_forms.EditSupplierPartForm
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Edit Supplier Part'


class SupplierPartCreate(AjaxCreateView):
    """ Create view for making new SupplierPart """

    model = SupplierPart
    form_class = part_forms.EditSupplierPartForm
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Create new Supplier Part'
    context_object_name = 'part'

    def get_form(self):
        """ Create Form instance to create a new SupplierPart object.
        Hide some fields if they are not appropriate in context
        """
        form = super(AjaxCreateView, self).get_form()
        
        if form.initial.get('supplier', None):
            # Hide the supplier field
            form.fields['supplier'].widget = HiddenInput()

        if form.initial.get('part', None):
            # Hide the part field
            form.fields['part'].widget = HiddenInput()

        return form

    def get_initial(self):
        """ Provide initial data for new SupplierPart:

        - If 'supplier_id' provided, pre-fill supplier field
        - If 'part_id' provided, pre-fill part field
        """
        initials = super(SupplierPartCreate, self).get_initial().copy()

        supplier_id = self.get_param('supplier')
        part_id = self.get_param('part')

        if supplier_id:
            try:
                initials['supplier'] = Company.objects.get(pk=supplier_id)
            except Company.DoesNotExist:
                initials['supplier'] = None
        
        if part_id:
            try:
                initials['part'] = Part.objects.get(pk=part_id)
            except Part.DoesNotExist:
                initials['part'] = None
        
        return initials


class SupplierPartDelete(AjaxDeleteView):
    """ Delete view for removing a SupplierPart """
    model = SupplierPart
    success_url = '/supplier/'
    ajax_template_name = 'company/partdelete.html'
    ajax_form_title = 'Delete Supplier Part'
    context_object_name = 'supplier_part'