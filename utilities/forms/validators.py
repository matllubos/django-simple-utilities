# coding: utf-8
from django.utils.translation import ugettext_lazy as _

class MultiFieldsValidator(object):
    
    fields = ()
    error_messages = {
        'invalid' : _(u'Value is not valid.')
    }
    
    def raise_error(self, form, error="invalid"):
        for field in self.fields:
            form._errors[field] = form.error_class([self.error_messages[error]])
            
    def validate(self, cleaned_data, form):
        return cleaned_data
    
    
        
