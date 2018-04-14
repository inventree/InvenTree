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

