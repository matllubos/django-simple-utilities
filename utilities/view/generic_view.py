# coding: utf-8
from django.views.generic import ListView, DetailView, TemplateView
from django.shortcuts import HttpResponseRedirect
from django.contrib import messages
from django.utils.encoding import force_unicode
from django.forms.widgets import Media
from django.utils.datastructures import SortedDict
from django.forms import formsets
from django.forms.formsets import BaseFormSet

class FormsMixin(object):
    success_url = None
    forms_class = {}
    initials = {}
    messages_valid = {}
    messages_invalid = {}
    
    readonly_forms = []
    forms = {}
    
    
    def get_messages_valid(self):
        return self.messages_valid
    
    def get_messages_invalid(self):
        return self.messages_invalid
    
    def get_valid_message(self, form, form_key):
        messages_valid = self.get_messages_valid()
        
        if messages_valid.get(form_key):
            return messages_valid.get(form_key)
        return messages_valid.get('default')
    
    def get_invalid_message(self, form, form_key):
        messages_invalid = self.get_messages_invalid()
        
        if messages_invalid.get(form_key):
            return messages_invalid.get(form_key)
        return messages_invalid.get('default')
    
    def form_invalid(self, form, form_key, message_text= None):
        message_text = message_text or self.get_invalid_message(form, form_key)
        if message_text:
            messages.error(
                self.request,
                force_unicode(message_text),
                extra_tags=form_key
            )
        return self.get(self.request)
    
    def form_valid(self, form, form_key, message_text = None):
        message_text = message_text or self.get_valid_message(form, form_key)
        if message_text:
            messages.success(
                self.request,
                force_unicode(message_text),
                extra_tags=form_key
            )
        return HttpResponseRedirect(self.get_success_url(form_key))
    
    def get_success_url(self, form_key):
        return self.success_url or ''
    
    def get_context_data(self, **kwargs):
        context = super(FormsMixin, self).get_context_data(**kwargs)
        forms = self.get_forms()
        context['forms'] = forms
        context['media'] = self.get_media(forms)
        return context
   
    def get_submit_key(self, form_key):
        return '%s-submit' % form_key
    
    def submit(self, forms):
        for key, val in forms.items():
            if isinstance(val, dict):
                out = self.submit(val)
                if out: return out
                
                if self.get_submit_key(key) in self.request.POST:
                    
                    valid = True
                    for sub_key, sub_val in val.items():
                        print sub_key
                        print sub_val.is_valid()
                        print sub_val.errors
                        
                        if not sub_val.is_valid():
                            valid = False
                                
                    val.errors = not valid    
                                    
                    if not valid: return self.form_invalid(val, key)
                    else: return self.form_valid(val, key)
            
            else:
                if self.get_submit_key(key) in self.request.POST:

                    if key in self.get_readonly_forms():
                        return self.form_valid(val, key)
        
                    if val.is_valid():
                        return self.form_valid(val, key)
                    else:
                        return self.form_invalid(val, key)
        
        return None
    
    def post(self, request, *args, **kwargs):
        return self.submit(self.get_forms()) or self.get(request, *args, **kwargs)
            

    def get_form_messages(self, tag):
        form_messages =[]
        for message in messages.get_messages(self.request):
            if (message.extra_tags == tag):
                form_messages.append(message)
        return form_messages
      
    def get_readonly_forms(self):
        return list(self.readonly_forms)
        
          
    def get_form(self, form_class, form_key):
        form = form_class(**self.get_form_kwargs(form_key))
        form.messages = self.get_form_messages(form_key)
        form.form_key = form_key
        
        if isinstance(form, BaseFormSet):
            if form.forms:
                form.fields = form.forms[0]
            
        if form_key in self.get_readonly_forms():
            self.set_form_readonly(form)
        
        form.submit_key = self.get_submit_key(form_key)
        return form
    
    def set_form_readonly(self, form):
        if isinstance(form, dict):
            for key, sub_form in form.items():
                self.set_form_readonly(sub_form)
            
        elif isinstance(form, BaseFormSet):
            for form in form.forms:
                self.set_form_readonly(form)
            
        else:
            for fkey, field in form.fields.items():
                field.widget.attrs['disabled'] = 'disabled'
        
        form.is_readonly = True
            
    def get_form_group(self, form_key, parent_key=None, forms_class= None):        
        if not forms_class:
            forms_class = self.get_forms_class()
        
        for key, val in forms_class.items():
            if key == form_key:
                return parent_key
            
            
            if isinstance(val, dict): 
                out = self.get_form_group(form_key, key, val)
                if out:
                    return out
        return None
        
        
    def get_form_kwargs(self, form_key):
        kwargs = {'initial': self.get_initial(form_key)}
        
        if self.request.method in ('POST', 'PUT') and (self.get_submit_key(form_key) in self.request.POST or self.get_submit_key(self.get_form_group(form_key)) in self.request.POST) and (not form_key in self.get_readonly_forms()): 
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        
        instance = self.get_instance(form_key)
        if instance:
            kwargs['instance'] = instance
        return kwargs
    
    def get_initial(self, form_key):
        return self.initials.get(form_key)
     
    def get_instance(self, form_key):
        return None
   
    def get_formset(self, forms_class, form_key):
        forms = SortedDict()
        for key, val in forms_class.items():
            if isinstance(val, dict):
                forms[key] = self.get_formset(val, key)
            else:
                forms[key] = self.get_form(val, key)

        if not hasattr(forms, 'is_readonly') and form_key in self.get_readonly_forms():
            self.set_form_readonly(forms)
        
        forms.submit_key = self.get_submit_key(form_key)
        forms.messages = self.get_form_messages(form_key)
        forms.formset = True
        return forms
     
    def get_forms(self):
        if not self.forms:
            forms = SortedDict()
            for key, val in self.get_forms_class().items():
                if isinstance(val, dict):
                    forms[key] = self.get_formset(val, key)
                else:
                    forms[key] = self.get_form(val, key)
            self.forms = forms
        return self.forms

    def get_forms_class(self):
        return self.forms_class
           
    def get_media(self, forms):
        media = Media()
        media.add_js(getattr(self.Media, 'js', []))
        media.add_css(getattr(self.Media, 'css', {}))
    
        for key, form in forms.items():
            if isinstance(form, dict):
                media += self.get_media(form)
            else:
                media += form.media
                
        return media
    
    class Media():
        js = []
        css = {'screen':[], 'print':[]}    
        

class DetailFormsView(FormsMixin, DetailView):
    pass
    
    
    
class ListFormsView(FormsMixin, ListView):
    pass
    
    
class FormsView(FormsMixin, TemplateView):
    pass
    