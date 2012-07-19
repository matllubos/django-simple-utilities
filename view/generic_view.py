# coding: utf-8
from django.views.generic import ListView, DetailView, TemplateView
from django.shortcuts import HttpResponseRedirect
from django.contrib import messages


class DetailFormsView(DetailView):
    success_url = None
    forms_class = {}
    initials = {}
    
    def form_invalid(self, form, form_key):
        return self.get(self.request)
    
    def form_valid(self, form, form_key):
        return HttpResponseRedirect('')
    
    def get_success_url(self):
        return self.success_url
    
    def get_context_data(self, **kwargs):
        context = super(DetailFormsView, self).get_context_data(**kwargs)
        context['forms'] = self.get_forms()
        return context
    
    def post(self, request, *args, **kwargs):
        forms = self.get_forms()
        for key, val in forms.items():
            if (key in self.request.POST):
                if (val.is_valid()):
                    return self.form_valid(val, key)
                else:
                    return self.form_invalid(val, key)

    def get_form_messages(self, tag):
        form_messages =[]
        for message in messages.get_messages(self.request):
            if (message.extra_tags == tag):
                form_messages.append(message)
        return form_messages
        
    def get_form(self, form_class, form_key):
        form = form_class(**self.get_form_kwargs(form_key))
        form.messages = self.get_form_messages(form_key)
        return form
    
    def get_form_kwargs(self, form_key):
        kwargs = {'initial': self.get_initial(form_key)}
        if self.request.method in ('POST', 'PUT') and form_key in self.request.POST:
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        return kwargs
    
    def get_initial(self, form_key):
        return self.initials.get(form_key)
        
    def get_forms(self):
        forms = {}
        for key, val in self.forms_class.items():
            forms[key] = self.get_form(val, key)
        return forms
    
    
    
class ListFormsView(ListView):
    success_url = None
    forms_class = {}
    initials = {}
    
    def form_invalid(self, form, form_key):
        return self.get(self.request)
    
    def form_valid(self, form, form_key):
        return HttpResponseRedirect('')
    
    def get_success_url(self):
        return self.success_url
    
    def get_context_data(self, **kwargs):
        context = super(ListFormsView, self).get_context_data(**kwargs)
        context['forms'] = self.get_forms()
        return context
    
    def post(self, request, *args, **kwargs):
        forms = self.get_forms()
        for key, val in forms.items():
            if (key in self.request.POST):
                if (val.is_valid()):
                    return self.form_valid(val, key)
                else:
                    return self.form_invalid(val, key)

    def get_form_messages(self, tag):
        form_messages =[]
        for message in messages.get_messages(self.request):
            if (message.extra_tags == tag):
                form_messages.append(message)
        return form_messages
        
    def get_form(self, form_class, form_key):
        form = form_class(**self.get_form_kwargs(form_key))
        form.messages = self.get_form_messages(form_key)
        return form
    
    def get_form_kwargs(self, form_key):
        kwargs = {'initial': self.get_initial(form_key)}
        if self.request.method in ('POST', 'PUT') and form_key in self.request.POST:
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        return kwargs
    
    def get_initial(self, form_key):
        return self.initials.get(form_key)
        
    def get_forms(self):
        forms = {}
        for key, val in self.forms_class.items():
            forms[key] = self.get_form(val, key)
        return forms
    
    
class FormsView(TemplateView):
    success_url = None
    forms_class = {}
    initials = {}
    
    def form_invalid(self, form, form_key):
        return self.get(self.request)
    
    def form_valid(self, form, form_key):
        return HttpResponseRedirect(self.success_url)
    
    def get_success_url(self):
        return self.success_url
    
    def get_context_data(self, **kwargs):
        context = super(FormsView, self).get_context_data(**kwargs)
        context['forms'] = self.get_forms()
        return context
    
    def post(self, request, *args, **kwargs):
        forms = self.get_forms()
        for key, val in forms.items():
            if (key in self.request.POST):
                if (val.is_valid()):
                    return self.form_valid(val, key)
                else:
                    return self.form_invalid(val, key)

    def get_form_messages(self, tag):
        form_messages =[]
        for message in messages.get_messages(self.request):
            if (message.extra_tags == tag):
                form_messages.append(message)
        return form_messages
        
    def get_form(self, form_class, form_key):
        form = form_class(**self.get_form_kwargs(form_key))
        form.messages = self.get_form_messages(form_key)
        return form
    
    def get_form_kwargs(self, form_key):
        kwargs = {'initial': self.get_initial(form_key)}
        if self.request.method in ('POST', 'PUT') and form_key in self.request.POST:
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        return kwargs
    
    def get_initial(self, form_key):
        return self.initials.get(form_key)
        
    def get_forms(self):
        forms = {}
        for key, val in self.forms_class.items():
            forms[key] = self.get_form(val, key)
        return forms