"""
Django views for interacting with Part app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import get_object_or_404

from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView
from django.forms.models import model_to_dict

from company.models import Company
from .models import PartCategory, Part, BomItem
from .models import SupplierPart

from .forms import PartImageForm
from .forms import EditPartForm
from .forms import EditCategoryForm
from .forms import EditBomItemForm
from .forms import BomExportForm

from .forms import EditSupplierPartForm

from InvenTree.views import AjaxView, AjaxCreateView, AjaxUpdateView, AjaxDeleteView

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


class PartCreate(AjaxCreateView):
    """ View for creating a new Part object.

    Options for providing initial conditions:
    
    - Provide a category object as initial data
    - Copy an existing Part
    """
    model = Part
    form_class = EditPartForm

    ajax_form_title = 'Create new part'
    ajax_template_name = 'modal_form.html'

    def get_data(self):
        return {
            'success': "Created new part",
        }

    def get_category_id(self):
        return self.request.GET.get('category', None)

    # If a category is provided in the URL, pass that to the page context
    def get_context_data(self, **kwargs):
        """ Provide extra context information for the form to display:

        - Add category information (if provided)
        """
        context = super(PartCreate, self).get_context_data(**kwargs)

        # Add category information to the page
        cat_id = self.get_category_id()

        if cat_id:
            context['category'] = get_object_or_404(PartCategory, pk=cat_id)

        return context

    # Pre-fill the category field if a valid category is provided
    def get_initial(self):
        """ Get initial data for the new Part object:

        - If a category is provided, pre-fill the Category field
        - If 'copy' parameter is provided, copy from referenced Part
        """

        # Is the client attempting to copy an existing part?
        part_to_copy = self.request.GET.get('copy', None)

        if part_to_copy:
            try:
                original = Part.objects.get(pk=part_to_copy)
                initials = model_to_dict(original)
                self.ajax_form_title = "Copy Part '{p}'".format(p=original.name)
            except Part.DoesNotExist:
                initials = super(PartCreate, self).get_initial()

        else:
            initials = super(PartCreate, self).get_initial()

        if self.get_category_id():
            initials['category'] = get_object_or_404(PartCategory, pk=self.get_category_id())

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

        return context


class PartImage(AjaxUpdateView):
    """ View for uploading Part image """

    model = Part
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Upload Part Image'
    form_class = PartImageForm

    def get_data(self):
        return {
            'success': 'Updated part image',
        }


class PartEdit(AjaxUpdateView):
    """ View for editing Part object """

    model = Part
    form_class = EditPartForm
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Edit Part Properties'
    context_object_name = 'part'


class BomExport(AjaxView):

    model = Part
    ajax_form_title = 'Export BOM'
    ajax_template_name = 'part/bom_export.html'
    context_object_name = 'part'
    form_class = BomExportForm

    def get_object(self):
        return get_object_or_404(Part, pk=self.kwargs['pk'])

    def get(self, request, *args, **kwargs):
        form = self.form_class()

        """
        part = self.get_object()

        context = {
            'part': part
        }

        if request.is_ajax():
            passs
        """

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
    form_class = EditCategoryForm
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Edit Part Category'

    def get_context_data(self, **kwargs):
        context = super(CategoryEdit, self).get_context_data(**kwargs).copy()

        context['category'] = get_object_or_404(PartCategory, pk=self.kwargs['pk'])

        return context


class CategoryDelete(AjaxDeleteView):
    """ Delete view to delete a PartCategory """
    model = PartCategory
    ajax_template_name = 'part/category_delete.html'
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
    form_class = EditCategoryForm

    def get_context_data(self, **kwargs):
        """ Add extra context data to template.

        - If parent category provided, pass the category details to the template
        """
        context = super(CategoryCreate, self).get_context_data(**kwargs).copy()

        parent_id = self.request.GET.get('category', None)

        if parent_id:
            context['category'] = get_object_or_404(PartCategory, pk=parent_id)

        return context

    def get_initial(self):
        """ Get initial data for new PartCategory

        - If parent provided, pre-fill the parent category
        """
        initials = super(CategoryCreate, self).get_initial().copy()

        parent_id = self.request.GET.get('category', None)

        if parent_id:
            initials['parent'] = get_object_or_404(PartCategory, pk=parent_id)

        return initials


class BomItemDetail(DetailView):
    """ Detail view for BomItem """
    context_object_name = 'item'
    queryset = BomItem.objects.all()
    template_name = 'part/bom-detail.html'


class BomItemCreate(AjaxCreateView):
    """ Create view for making a new BomItem object """
    model = BomItem
    form_class = EditBomItemForm
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Create BOM item'

    def get_initial(self):
        """ Provide initial data for the BomItem:

        - If 'parent' provided, set the parent part field
        """

        # Look for initial values
        initials = super(BomItemCreate, self).get_initial().copy()

        # Parent part for this item?
        parent_id = self.request.GET.get('parent', None)

        if parent_id:
            initials['part'] = get_object_or_404(Part, pk=parent_id)

        return initials


class BomItemEdit(AjaxUpdateView):
    """ Update view for editing BomItem """

    model = BomItem
    form_class = EditBomItemForm
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
    form_class = EditSupplierPartForm
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Edit Supplier Part'


class SupplierPartCreate(AjaxCreateView):
    """ Create view for making new SupplierPart """

    model = SupplierPart
    form_class = EditSupplierPartForm
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Create new Supplier Part'
    context_object_name = 'part'

    def get_initial(self):
        """ Provide initial data for new SupplierPart:

        - If 'supplier_id' provided, pre-fill supplier field
        - If 'part_id' provided, pre-fill part field
        """
        initials = super(SupplierPartCreate, self).get_initial().copy()

        supplier_id = self.request.GET.get('supplier', None)
        part_id = self.request.GET.get('part', None)

        if supplier_id:
            initials['supplier'] = get_object_or_404(Company, pk=supplier_id)
            # TODO
            # self.fields['supplier'].disabled = True
        if part_id:
            initials['part'] = get_object_or_404(Part, pk=part_id)
            # TODO
            # self.fields['part'].disabled = True

        return initials


class SupplierPartDelete(AjaxDeleteView):
    """ Delete view for removing a SupplierPart """
    model = SupplierPart
    success_url = '/supplier/'
    ajax_template_name = 'company/partdelete.html'
