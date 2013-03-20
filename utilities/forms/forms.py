# coding: utf-8
from django.forms.models import ModelForm
from django import forms
from django.utils.translation import ugettext_lazy as _

class RequiredModelForm(ModelForm):
    
    
    def __init__(self, *args, **kwargs):
        super(RequiredModelForm, self).__init__(*args, **kwargs)
        for required_field in self.Meta.required_fields:
            self.fields[required_field].required = True
            
class InvoiceOrderInlineFormset(forms.models.BaseInlineFormSet):
    def is_valid(self):
        return super(InvoiceOrderInlineFormset, self).is_valid() and \
                    not any([bool(e) for e in self.errors])

    def clean(self):
        # get forms that actually have valid data
        count = 0
        for form in self.forms:
            try:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    count += 1
            except AttributeError:
                # annoyingly, if a subform is invalid Django explicity raises
                # an AttributeError for cleaned_data
                pass
        if count < 1:
            raise forms.ValidationError(_(u'Nejméně jedna položka musí být vyplněna'))