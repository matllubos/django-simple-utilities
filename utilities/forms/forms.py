# coding: utf-8
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

class InitialModelForm(ModelForm):
    
    initial_values = {}
    
    def __init__(self, data=None, files=None, initial=None):
        data = self.remove_initial_values(data)
        ModelForm.__init__(self, data=data, files=files, initial=initial)
        self.set_initial_values()
        
           
    def set_initial_values(self):
        for key, val in self.initial_values.items():
            if (self.fields[key].__class__.__name__ in ('TypedChoiceField', 'ModelChoiceField')):
                choices =  list(self.fields[key].widget.choices) 
                choices[0] = ('', val)
                self.fields[key].widget.choices = choices
            else:
                self.fields[key].initial = val
            self.fields[key].widget.attrs['title'] = val
     
    def remove_initial_values(self, data):
        if (data):
            data = data.copy()
            for key, val in self.initial_values.items():
                if (data.get(key) == val):
                    data[key] = ''
        return data
                       
            
class MultiFieldsValidationModelForm(ModelForm):
    validators = ()
    
    
    def clean(self):
        cleaned_data = super(MultiFieldsValidationModelForm, self).clean()
        for validator in self.validators:
            try:
                validator().validate(cleaned_data, self)
            except KeyError:
                pass
        return cleaned_data
    
    