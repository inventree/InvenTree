# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.template.loader import render_to_string
from django.http import JsonResponse

from django.views import View
from django.views.generic import UpdateView, CreateView, DeleteView
from rest_framework import views
from django.http import JsonResponse


class TreeSerializer(views.APIView):

    def itemToJson(self, item):

        data = {
            'text': item.name,
            'href': item.get_absolute_url(),
        }

        if item.has_children:
            nodes = []

            for child in item.children.all().order_by('name'):
                nodes.append(self.itemToJson(child))

            data['nodes'] = nodes

        return data

    def get(self, request, *args, **kwargs):

        top_items = self.model.objects.filter(parent=None).order_by('name')

        nodes = []

        for item in top_items:
            nodes.append(self.itemToJson(item))

        top = {
            'text': self.title,
            'nodes': nodes,
        }

        response = {
            'tree': [top]
        }

        return JsonResponse(response, safe=False)


class AjaxMixin(object):

    ajax_form_action = ''
    ajax_form_title = ''
    ajax_submit_text = 'Submit'

    def get_data(self):
        return {}

    def getAjaxTemplate(self):
        if hasattr(self, 'ajax_template_name'):
            return self.ajax_template_name
        else:
            return self.template_name

    def renderJsonResponse(self, request, form, data={}):

        context = {}

        if form:
            context['form'] = form

        data['title'] = self.ajax_form_title

        data['submit_text'] = self.ajax_submit_text

        data['html_form'] = render_to_string(
            self.getAjaxTemplate(),
            context,
            request=request
        )

        # Custom feedback`data
        fb = self.get_data()

        for key in fb.keys():
            data[key] = fb[key]

        return JsonResponse(data, safe=False)


class AjaxView(AjaxMixin, View):
    """ Bare-bones AjaxView """

    def post(self, request, *args, **kwargs):
        return JsonResponse('', safe=False)

    def get(self, request, *args, **kwargs):

        return self.renderJsonResponse(request, None)


class AjaxCreateView(AjaxMixin, CreateView):

    def post(self, request, *args, **kwargs):
        form = self.form_class(data=request.POST, files=request.FILES)

        if request.is_ajax():

            data = {'form_valid': form.is_valid()}

            if form.is_valid():
                obj = form.save()

                # Return the PK of the newly-created object
                data['pk'] = obj.pk

                data['url'] = obj.get_absolute_url()

            return self.renderJsonResponse(request, form, data)

        else:
            return super(CreateView, self).post(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):

        response = super(CreateView, self).get(request, *args, **kwargs)

        if request.is_ajax():
            form = self.form_class(initial=self.get_initial())

            return self.renderJsonResponse(request, form)

        else:
            return response


class AjaxUpdateView(AjaxMixin, UpdateView):

    def post(self, request, *args, **kwargs):

        form = self.form_class(instance=self.get_object(), data=request.POST, files=request.FILES)

        if request.is_ajax():

            data = {'form_valid': form.is_valid()}

            if form.is_valid():
                obj = form.save()

                data['pk'] = obj.id
                data['url'] = obj.get_absolute_url()

            response = self.renderJsonResponse(request, form, data)
            return response

        else:
            return response

    def get(self, request, *args, **kwargs):

        response = super(UpdateView, self).get(request, *args, **kwargs)

        if request.is_ajax():
            form = self.form_class(instance=self.get_object())

            return self.renderJsonResponse(request, form)

        else:
            return super(UpdateView, self).post(request, *args, **kwargs)


class AjaxDeleteView(AjaxMixin, DeleteView):

    def post(self, request, *args, **kwargs):

        if request.is_ajax():
            obj = self.get_object()
            pk = obj.id
            obj.delete()

            data = {'id': pk,
                    'delete': True}

            return self.renderJsonResponse(request, None, data)

        else:
            return super(DeleteView, self).post(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):

        response = super(DeleteView, self).get(request, *args, **kwargs)

        if request.is_ajax():

            data = {'id': self.get_object().id,
                    'title': self.ajax_form_title,
                    'delete': False,
                    'html_data': render_to_string(self.getAjaxTemplate(),
                                                  self.get_context_data(),
                                                  request=request)
                    }

            return JsonResponse(data)

        else:
            return response
