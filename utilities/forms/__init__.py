# coding: utf-8
import re

from django.utils.encoding import smart_str
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from utilities.forms.widgets import FullSizeMultipleSelectWidget,  OtherSelectWidget

class CommaDecimalField(forms.FloatField):

    def clean(self, value):
        value = smart_str(value).replace(',', '.')
        return super(CommaDecimalField, self).clean(value)
    
class StylizedIntegerField(forms.IntegerField):
    
    def clean(self, value):
        value = smart_str(value).replace(' ', '')
        return super(StylizedIntegerField, self).clean(value)
    
    
class GoogleMapUrlFormField(forms.URLField):
    def clean(self, value):
        m = re.match(r"^.*src=\"([^\"]+)\".*$", value)
        if (m):
            value = m.group(1)
        if (not re.search(r"output\=embed", value)):
            value += '&amp;output=embed'

        if (not re.search(r"^https?://maps\.google\.cz/maps", value)):
            raise ValidationError(_(u'Toto není správné URL google map'))
        return super(GoogleMapUrlFormField, self).clean(value) 
   
class FullSizeModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    widget = FullSizeMultipleSelectWidget
    
class OtherSelectField(forms.MultiValueField):

    def __init__(self, choices=[], other_label=_(u'Other'), *args, **kwargs):
        fields = (forms.CharField(required=True),
                  forms.CharField(required=False, max_length = kwargs['max_length']),)
        del kwargs['max_length']
        del kwargs['widget']
        self.fields = fields
        
        super(forms.MultiValueField, self).__init__(widget = OtherSelectWidget(choices, other_label), *args, **kwargs)

    def clean(self, value):
        if not value:
            if self.required:
                raise ValidationError(self.error_messages['required'])

        out = self.compress(value)
        self.validate(out)
        return out
    
    def compress(self, data_list):
        if data_list:
            if (data_list[0] == '__other__'):
                return data_list[1]
            return data_list[0]
        return None