from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect

from django.views.generic import DetailView, ListView
from django.views.generic.edit import UpdateView, DeleteView, CreateView

from part.models import Part
from .models import UniquePart

from .forms import EditTrackedPartForm


class TrackIndex(ListView):
    model = UniquePart
    template_name = 'track/index.html'
    context_object_name = 'parts'
    paginate_by = 50

    def get_queryset(self):
        return UniquePart.objects.order_by('part__name', 'serial')


class TrackDetail(DetailView):
    queryset = UniquePart.objects.all()
    template_name = 'track/detail.html'
    context_object_name = 'part'


class TrackCreate(CreateView):
    model = UniquePart
    form_class = EditTrackedPartForm
    template_name = 'track/create.html'
    context_object_name = 'part'

    def get_initial(self):
        initials = super(TrackCreate, self).get_initial().copy()

        part_id = self.request.GET.get('part', None)

        if part_id:
            initials['part'] = get_object_or_404(Part, pk=part_id)

        return initials


class TrackEdit(UpdateView):
    model = UniquePart
    form_class = EditTrackedPartForm
    template_name = 'track/edit.html'
    context_obect_name = 'part'


class TrackDelete(DeleteView):
    model = UniquePart
    success_url = '/track'
    template_name = 'track/delete.html'
    context_object_name = 'track'

    def post(self, request, *args, **kwargs):
        if 'confirm' in request.POST:
            return super(TrackDelete, self).post(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(self.get_object().get_absolute_url())
