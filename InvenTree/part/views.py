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

from InvenTree.helpers import DownloadFile


class PartIndex(ListView):
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
    """ Create a new part
    - Optionally provide a category object as initial data
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
        context = super(PartCreate, self).get_context_data(**kwargs)

        # Add category information to the page
        cat_id = self.get_category_id()

        if cat_id:
            context['category'] = get_object_or_404(PartCategory, pk=cat_id)

        return context

    # Pre-fill the category field if a valid category is provided
    def get_initial(self):

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
    context_object_name = 'part'
    queryset = Part.objects.all()
    template_name = 'part/detail.html'

    # Add in some extra context information based on query params
    def get_context_data(self, **kwargs):
        context = super(PartDetail, self).get_context_data(**kwargs)

        if self.request.GET.get('edit', '').lower() in ['true', 'yes', '1']:
            context['editing_enabled'] = 1
        else:
            context['editing_enabled'] = 0

        return context


class PartImage(AjaxUpdateView):

    model = Part
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Upload Part Image'
    form_class = PartImageForm

    def get_data(self):
        return {
            'success': 'Updated part image',
        }


class PartEdit(AjaxUpdateView):
    model = Part
    template_name = 'part/edit.html'
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
    model = Part
    template_name = 'part/delete.html'
    ajax_template_name = 'part/partial_delete.html'
    ajax_form_title = 'Confirm Part Deletion'
    context_object_name = 'part'

    success_url = '/part/'

    def get_data(self):
        return {
            'danger': 'Part was deleted',
        }


class CategoryDetail(DetailView):
    model = PartCategory
    context_object_name = 'category'
    queryset = PartCategory.objects.all()
    template_name = 'part/category.html'


class CategoryEdit(AjaxUpdateView):
    model = PartCategory
    template_name = 'part/category_edit.html'
    form_class = EditCategoryForm
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Edit Part Category'

    def get_context_data(self, **kwargs):
        context = super(CategoryEdit, self).get_context_data(**kwargs).copy()

        context['category'] = get_object_or_404(PartCategory, pk=self.kwargs['pk'])

        return context


class CategoryDelete(AjaxDeleteView):
    model = PartCategory
    template_name = 'part/category_delete.html'
    context_object_name = 'category'
    success_url = '/part/'

    def get_data(self):
        return {
            'danger': 'Part category was deleted',
        }


class CategoryCreate(AjaxCreateView):
    model = PartCategory
    ajax_form_action = reverse_lazy('category-create')
    ajax_form_title = 'Create new part category'
    ajax_template_name = 'modal_form.html'
    template_name = 'part/category_new.html'
    form_class = EditCategoryForm

    def get_context_data(self, **kwargs):
        context = super(CategoryCreate, self).get_context_data(**kwargs).copy()

        parent_id = self.request.GET.get('category', None)

        if parent_id:
            context['category'] = get_object_or_404(PartCategory, pk=parent_id)

        return context

    def get_initial(self):
        initials = super(CategoryCreate, self).get_initial().copy()

        parent_id = self.request.GET.get('category', None)

        if parent_id:
            initials['parent'] = get_object_or_404(PartCategory, pk=parent_id)

        return initials


class BomItemDetail(DetailView):
    context_object_name = 'item'
    queryset = BomItem.objects.all()
    template_name = 'part/bom-detail.html'


class BomItemCreate(AjaxCreateView):
    model = BomItem
    form_class = EditBomItemForm
    template_name = 'part/bom-create.html'
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Create BOM item'

    def get_initial(self):
        # Look for initial values
        initials = super(BomItemCreate, self).get_initial().copy()

        # Parent part for this item?
        parent_id = self.request.GET.get('parent', None)

        if parent_id:
            initials['part'] = get_object_or_404(Part, pk=parent_id)

        return initials


class BomItemEdit(AjaxUpdateView):
    model = BomItem
    form_class = EditBomItemForm
    template_name = 'part/bom-edit.html'
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Edit BOM item'


class BomItemDelete(AjaxDeleteView):
    model = BomItem
    template_name = 'part/bom-delete.html'
    context_object_name = 'item'
    ajax_form_title = 'Confim BOM item deletion'


class SupplierPartDetail(DetailView):
    model = SupplierPart
    template_name = 'company/partdetail.html'
    context_object_name = 'part'
    queryset = SupplierPart.objects.all()


class SupplierPartEdit(AjaxUpdateView):
    model = SupplierPart
    template_name = 'company/partedit.html'
    context_object_name = 'part'
    form_class = EditSupplierPartForm
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Edit Supplier Part'


class SupplierPartCreate(AjaxCreateView):
    model = SupplierPart
    form_class = EditSupplierPartForm
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Create new Supplier Part'
    context_object_name = 'part'

    def get_initial(self):
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
    model = SupplierPart
    success_url = '/supplier/'
    template_name = 'company/partdelete.html'
