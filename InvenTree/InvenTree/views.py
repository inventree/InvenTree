# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.template.loader import render_to_string
from django.http import JsonResponse

from django.views.generic import UpdateView, CreateView, DeleteView


class AjaxView(object):

    ajax_form_action = ''
    ajax_form_title = ''
    ajax_submit_text = 'Submit'

    def getAjaxTemplate(self):
        if hasattr(self, 'ajax_template_name'):
            return self.ajax_template_name
        else:
            return self.template_name


    def renderJsonResponse(self, request, form, data={}):

        context = {'form': form,
                   'form_action': self.ajax_form_action,
                   'form_title': self.ajax_form_title,
                   'submit_text': self.ajax_submit_text,
                  }

        data['html_form'] = render_to_string(
            self.getAjaxTemplate(),
            context,
            request=request
        )

        return JsonResponse(data)


class AjaxCreateView(AjaxView, CreateView):

    def post(self, request):

        if request.is_ajax():
            form = self.form_class(request.POST)

            data = {'form_valid': form.is_valid()}

            if form.is_valid():
                obj = form.save()

                # Return the PK of the newly-created object
                data['pk']  = obj.pk

            return self.renderJsonResponse(request, form, data)

        else:
            return super(CreateView, self).post(request)

    def get(self, request):

        response = super(CreateView, self).get(request)

        if request.is_ajax():
            form = self.form_class(initial=self.get_initial())

            return self.renderJsonResponse(request, form)

        else:
            return response
