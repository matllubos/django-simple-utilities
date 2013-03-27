# coding: utf-8
import re

from django.utils.encoding import smart_str, smart_unicode
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.forms.models import ModelChoiceIterator, ModelForm
from django.utils.safestring import mark_safe
from django.core import validators
from django.core.validators import EmailValidator, BaseValidator
from django.contrib.localflavor.cz import forms as localforms

from utilities.forms.widgets import FullSizeMultipleSelectWidget,  OtherSelectWidget, MultipleOptgroupSelect,\
    DatepickerWidget, WidgetFactory, FieldsWidget
from django.forms.fields import RegexField


class CommaDecimalField(forms.FloatField):

    def clean(self, value):
        value = smart_str(value).replace(',', '.')
        return super(CommaDecimalField, self).clean(value)
    
class StylizedIntegerField(forms.IntegerField):
    
    def clean(self, value):
        value = smart_str(value).replace(' ', '')
        return super(StylizedIntegerField, self).clean(value)
    
    
class GoogleMapUrlField(forms.URLField):
    def clean(self, value):
        m = re.match(r"^.*src=\"([^\"]+)\".*$", value)
        if (m):
            value = m.group(1)
        if (not re.search(r"output\=embed", value)):
            value += '&amp;output=embed'

        if (not re.search(r"^https?://maps\.google\.cz/maps", value)):
            raise ValidationError(_(u'This is not Google maps URL.'))
        return super(GoogleMapUrlField, self).clean(value) 


class GoogleSpreadsheetField(forms.CharField):
    def clean(self, value):
        value = re.sub(r'^.*\?key=([^&#"]*).*$',r'\g<1>', value)
        return super(GoogleSpreadsheetField, self).clean(value) 


class FullSizeModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    widget = FullSizeMultipleSelectWidget
    
class OtherSelectField(forms.MultiValueField):

    def __init__(self, choices=[], other_label=_(u'Other'), hide_relations=None, *args, **kwargs):
        fields = (forms.CharField(required=True),
                  forms.CharField(required=False, max_length = kwargs['max_length']),)
        del kwargs['max_length']
        kwargs['widget'] = OtherSelectWidget(choices, other_label, hide_relations=hide_relations)
        self.fields = fields
        super(forms.MultiValueField, self).__init__(*args, **kwargs)

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


class TreeModelChoiceIterator(ModelChoiceIterator):
    def __init__(self, parent, *args, **kwargs):
        super(TreeModelChoiceIterator, self).__init__(*args, **kwargs)
        self.parent = parent

    def tree_sort(self, parent):
        result = []
        filter_values = {self.parent: parent}
        
        ordering = self.queryset.model._meta.ordering
         
        qs = self.queryset.filter(**filter_values)
        if (ordering):
            qs.order_by(*ordering)
        for obj in qs:
            result = result + [obj] + self.tree_sort(obj)
        return result
    
    def get_depth(self, obj):
        depth = 0
        parent =  getattr(obj, self.parent)
        obj.parent
        while(parent != None):
            parent = getattr(parent, self.parent)
            depth += 1
        return depth
    
    def __iter__(self):
        if self.field.empty_label is not None:
            yield (u"", self.field.empty_label)
        if self.field.cache_choices:
            if self.field.choice_cache is None:
                self.field.choice_cache = [
                    self.choice(obj) for obj in self.tree_sort(None)
                ]
            for choice in self.field.choice_cache:
                yield choice
        else:
            for obj in self.tree_sort(None):
                yield self.choice(obj)
                
     
    def choice(self, obj):
        return (self.field.prepare_value(obj), mark_safe(u'%s|- %s' % ('&nbsp;' * self.get_depth(obj) * 2, self.field.label_from_instance(obj)))) 
              
class TreeModelChoiceField(forms.ModelChoiceField):
    def __init__(self, queryset, parent, *args, **kwargs):
        self.parent = parent
        super(TreeModelChoiceField, self).__init__(queryset, *args, **kwargs)

    def _get_choices(self):
        if hasattr(self, '_choices'):
            return self._choices
        return TreeModelChoiceIterator(self.parent, self)
    choices = property(_get_choices, forms.ChoiceField._set_choices)  
  
  
class GroupsModelChoiceIterator(ModelChoiceIterator):
    def __init__(self, group_by, order_by, *args, **kwargs):
        super(GroupsModelChoiceIterator, self).__init__(*args, **kwargs)
        self.group_by = group_by
        self.order_by = order_by
    
    def __iter__(self):
        if self.field.empty_label is not None:
            yield (u"", self.field.empty_label)
        if self.field.cache_choices:
            if self.field.choice_cache is None:
                self.field.choice_cache = [
                    self.choice(obj) for obj in self.queryset.all()
                ]
            for choice in self.field.choice_cache:
                yield choice
        else:
            group = []
            
            order_by = list(self.group_by) + list(self.order_by)      
            for obj in self.queryset.all().order_by(*order_by):
                current_group = group
                prev_group = None
                i = 0 
                for group_name in self.group_by:
                    if current_group and group_name == self.group_by[0] and getattr(obj, group_name) != current_group[0]:
                        yield group
                        current_group = group = []

                    if not current_group or getattr(obj, group_name) != current_group[0]:
                        current_group = (getattr(obj, group_name), [])
                        if prev_group:
                            
                            prev_group[1].append(current_group)
                        else:
                            group = current_group
                            
                        prev_group = current_group
                        current_group = ()
                    else:
                        prev_group = current_group
                        current_group = current_group[1][-1]
                    i+= 1
                prev_group[1].append(self.choice(obj))
            if group:
                yield group
        
      
class GroupsModelChoiceField(forms.ModelChoiceField):
    def __init__(self, queryset, group_by,  order_by, *args, **kwargs):
        self.group_by = group_by
        self.order_by = order_by
        super(GroupsModelChoiceField, self).__init__(queryset, *args, **kwargs)

    def _get_choices(self):
        if hasattr(self, '_choices'):
            return self._choices
        return GroupsModelChoiceIterator(self.group_by, self.order_by, self)
    choices = property(_get_choices, forms.ChoiceField._set_choices)  


class NotRegexValidator(validators.RegexValidator):
    def __call__(self, value):
        if self.regex.search(smart_unicode(value)):
            raise validators.ValidationError(self.message, code=self.code)
     
class CzPhoneFormField(forms.RegexField):
    def __init__(self, max_length=None, min_length=None, error_message=None, *args, **kwargs):
        codes = ['601', '602', '606', '607', '702', '720', '721', '722', '723', '724', '725', '726', '727', '728', '729',
                 '603', '604', '605', '730', '731', '732', '733', '734', '736', '737', '738', '739',
                 '608', '770', '773', '774', '775', '776', '777',
                 '790',
                 '797',
                 '791',
                 '799',
                 '2\d\d', '31\d', '32\d', '35\d', '37\d', '38\d', '39\d', '41\d', '47\d', '46\d', '48\d', '49\d', 
                 '51\d', '53\d', '54\d', '55\d', '59\d', '56\d', '57\d', '58\d'  ]
        
        
        regex = r'^(\+?\d{3})? ?(%s) ?\d{3} ?\d{3}$' % ('|').join(codes)
        
        
        super(CzPhoneFormField, self).__init__(regex, max_length, min_length, error_message = _(u'Enter a valid phone number'), *args, **kwargs)
        invalid_numbers = []
        for i in range(0, 9):
            invalid_numbers.append('((\+?\d{3})? ?%s{3} ?%s{3} ?%s{3})' % (i,i,i))
        
        invalid_numbers.append('((\+?\d{3})? ?123 ?456 ?789)')
        invalid_numbers.append('((\+?\d{3})? ?987 ?654 ?321)')
        self.validators.append(NotRegexValidator(regex='%s' % '|'.join(invalid_numbers)))  

    def clean(self, value):
        if value == '+420':
            value = ''
        return super(CzPhoneFormField, self).clean(value)

class AutoFormatIntegerField(forms.IntegerField):
    
    def __init__(self, *args, **kwargs):
        super(AutoFormatIntegerField, self).__init__(*args, **kwargs)

            
    def clean(self, value):
        value = smart_str(value).replace(' ', '')
        return super(AutoFormatIntegerField, self).clean(value)   
 
email_re = re.compile(
    r"(^[0-9A-Z]+([-\._][0-9A-Z]+)*"  # dot-atom
    r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"' # quoted-string
    r')@(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?$', re.IGNORECASE)  # domain
validate_email = EmailValidator(email_re, _(u'Enter a valid e-mail address.'), 'invalid')
   
class StrictEmailField(forms.EmailField):
    default_validators = [validate_email]        
    
    
    
class InitialModelForm(ModelForm):
    
    initial_values = {}
    
    def __init__(self, data=None, files=None, initial=None):
        data = self.remove_initial_values(data)
        ModelForm.__init__(self, data=data, files=files, initial=initial)
        self.set_initial_values()
        
           
    def set_initial_values(self):
        for key, val in self.initial_values.items():        
            self.set_inital_value(key, val)
     
    
    def set_inital_value(self, key, val):
        if hasattr(self.fields[key].widget, 'choices'):
            choices =  list(self.fields[key].widget.choices) 
            if choices[0][0] == '':
                choices[0] = ('', val)
            else:
                choices.insert(0, ('', val))
            self.fields[key].widget.choices = choices
        else:
            self.fields[key].initial = val
        self.fields[key].widget.attrs['title'] = val
        class_names = self.fields[key].widget.attrs.get('class', None)
        if class_names:
            class_names += ' initial'
        else:
            class_names = 'initial'
        self.fields[key].widget.attrs['class']= class_names       
            
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

class AntispamField(forms.IntegerField):
    def __init__(self, *args, **kwargs):
        kwargs['label'] = '1+1=?'
        super(AntispamField, self).__init__(*args,**kwargs)
        self.validators.append(BaseValidator(2))
        self.widget.attrs['class'] = 'antispam'


class DatepickerField(forms.DateField):
    widget = DatepickerWidget
    
    def widget_attrs(self, widget):
        return {'class': 'datepicker-widget'}
    
    
        
class ICQNumberField(RegexField):
    default_error_messages = {
        'invalid': _(u'Enter an ICQ number in the format XXXXXXXXX.'),
        }
    def __init__(self, max_length=None, min_length=None, *args, **kwargs):
        super(ICQNumberField, self).__init__(r'\d{5,32}$',
            max_length, min_length, *args, **kwargs)

    
class CZBirthNumberField(localforms.CZBirthNumberField):
    
    def __init__(self, max_length=None, *args, **kwargs): 
        super(CZBirthNumberField, self).__init__(*args, **kwargs)
        
class CZDICField(RegexField):
    
    def __init__(self, *args, **kwargs):
        super(CZDICField, self).__init__(r'^[a-zA-Z]{2}\d{8,10}$', *args, **kwargs)
        
        
class CZICNumberField(localforms.CZICNumberField):
    def __init__(self, max_length=None, *args, **kwargs): 
        super(CZICNumberField, self).__init__(*args, **kwargs)
        
class PSCField(forms.RegexField):
    def __init__(self, *args, **kwargs):
        kwargs['widget'] = WidgetFactory().create(FieldsWidget, {'class': 'psc'}, kwargs.get('widget', None))
        super(PSCField, self).__init__(r'^\d{3} ?\d{2}$', *args, **kwargs)
    