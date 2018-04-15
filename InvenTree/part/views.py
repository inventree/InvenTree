from InvenTree.models import FilterChildren
from .models import PartCategory, Part

from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse

from django.views.generic import DetailView, ListView
from django.views.generic.edit import UpdateView, DeleteView, CreateView

from .forms import EditPartForm

class PartIndex(ListView):
    model = Part
    template_name = 'part/index.html'
    context_object_name = 'parts'

    def get_queryset(self):
        self.category = self.request.GET.get('category', None)

        return Part.objects.filter(category=self.category)

    def get_context_data(self, **kwargs):

        context = super(PartIndex, self).get_context_data(**kwargs)

        children = PartCategory.objects.filter(parent=self.category)

        context['children'] = children

        if self.category:
            context['category'] = get_object_or_404(PartCategory, pk=self.category)

        return context


class PartCreate(CreateView):
    """ Create a new part
    - Optionally provide a category object as initial data
    """
    model = Part
    form_class = EditPartForm
    template_name = 'part/create.html'

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

        initials = super(PartCreate, self).get_initial().copy()

        if self.get_category_id():
            initials['category'] = get_object_or_404(PartCategory, pk=self.get_category_id())

        return initials


class PartDetail(DetailView):
    context_object_name = 'part'
    queryset = Part.objects.all()
    template_name = 'part/detail.html'


class PartEdit(UpdateView):
    model = Part
    form_class = EditPartForm
    template_name = 'part/edit.html'


class PartDelete(DeleteView):
    model = Part
    template_name = 'part/delete.html'

    success_url = '/part/'

    def post(self, request, *args, **kwargs):
        if 'confirm' in request.POST:
            return super(PartDelete, self).post(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(self.get_object().get_absolute_url())

