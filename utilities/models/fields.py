# coding: utf-8
import re

from datetime import date

from django.db import models
from django import forms
from django.db.models.fields import PositiveIntegerField, BLANK_CHOICE_DASH
from django.core import validators     , exceptions
from django.utils.translation import ugettext_lazy as _
from django.db.models.fields.files import FieldFile
from django.conf import settings
from django.utils.functional import curry

from sorl.thumbnail import ImageField

from utilities.utils import fit
from utilities.forms.widgets import CommaWidget, WidgetFactory, FieldsWidget, HtmlWidget, MeasureWidget, SelectMonthYearWidget, OrderWidget,\
    HideSelectWidget, CommaMeasureWidget
from utilities.forms import CommaDecimalField, StylizedIntegerField, GoogleMapUrlFormField, FullSizeModelMultipleChoiceField, OtherSelectField, TreeModelChoiceField,\
    CzPhoneFormField, AutoFormatIntegerField
from django.utils.encoding import smart_unicode


class FieldError(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)
        
class IntegerField(models.IntegerField):
    def __init__(self, verbose_name=None, name=None, min_value=None, max_value=None, measure=None, auto_format=False, **kwargs):
        self.min_value, self.max_value = min_value, max_value
        self.measure = measure
        self.auto_format = auto_format
        models.IntegerField.__init__(self, verbose_name, name, **kwargs)
    
    def formfield(self, **kwargs):
        defaults = {'min_value': self.min_value, 'max_value':self.max_value}
        class_names = ['integer']
        
        if self.auto_format:
            class_names.append('auto-format')
            defaults = {'form_class': AutoFormatIntegerField}
         
        defaults.update(kwargs)
        defaults['widget'] = WidgetFactory().create(MeasureWidget, {'class': ' '.join(class_names)}, kwargs.get('widget', None), measure=self.measure)
        
        return super(IntegerField, self).formfield(**defaults)
    
class PositiveIntegerField(IntegerField):
    def __init__(self, verbose_name=None, name=None, min_value=0, max_value=None, measure=None, auto_format=False, **kwargs):
            if min_value < 0:
                raise FieldError('min_value must be greater than 0')
            super(PositiveIntegerField, self).__init__(verbose_name=verbose_name, name=name, min_value=min_value, max_value=max_value, measure=measure, auto_format=auto_format, **kwargs)
 
 
class FloatField(models.FloatField):
    def __init__(self, verbose_name=None, name=None, min_value=None, max_value=None, measure=None, comma=True, **kwargs):
        self.min_value, self.max_value = min_value, max_value
        self.measure = measure
        self.comma = comma
        models.FloatField.__init__(self, verbose_name, name, **kwargs)
    
    def formfield(self, **kwargs):
        defaults = {'min_value': self.min_value, 'max_value':self.max_value}
        defaults.update(kwargs)
        if self.comma:
            defaults['widget'] = WidgetFactory().create(CommaMeasureWidget, {'class': 'float'}, kwargs.get('widget', None), measure=self.measure)
            return super(FloatField, self).formfield(form_class=CommaDecimalField, **defaults)
        defaults['widget'] = WidgetFactory().create(MeasureWidget, {'class': 'float'}, kwargs.get('widget', None), measure=self.measure) 
        return super(FloatField, self).formfield(**defaults)
 
 
class PhoneField(models.CharField):
    
    def __init__(self, verbose_name=None, name=None, format='CZ', **kwargs):
        if (format == 'CZ'):
            models.CharField.__init__(self, verbose_name, name ,max_length=16, **kwargs)
        elif (format == 'DE'):
            models.CharField.__init__(self, verbose_name, name ,max_length=21, **kwargs)
        else:
            models.CharField.__init__(self, verbose_name, name ,max_length=50, **kwargs)
        self.format = format
        
    def formfield(self, **kwargs):
        form_class = forms.RegexField
        if (self.format == 'CZ'):
            defaults = {}
            form_class=CzPhoneFormField
        elif (self.format == 'DE'):
            defaults = {'regex':r'^(((((((00|\+)49[ \-/]?)|0)[1-9][0-9]{1,4})[ \-/]?)|((((00|\+)49\()|\(0)[1-9][0-9]{1,4}\)[ \-/]?))[0-9]{1,7}([ \-/]?[0-9]{1,5})?)$',} 
        elif (self.format == 'OPEN'):
            defaults = {'regex':r'^[\+\d\-\(\) ]+$',} 
        
        defaults.update(kwargs)
        defaults['widget'] = WidgetFactory().create(FieldsWidget, {'class': '%s-phone' % self.format}, kwargs.get('widget', None))
        return super(models.CharField, self).formfield(form_class=form_class, **defaults)
   
    def pre_save(self, model_instance, add):
        if (self.format == 'CZ' and getattr(model_instance, self.attname)):
            m = re.match(r'^(\+?\d{3})? ?(\d{3}) ?(\d{3}) ?(\d{3})$', getattr(model_instance, self.attname))
            out = '+420'
            if (m.group(1)): out = '+'+re.sub(r'\+', '', m.group(1))
            return '{0} {1} {2} {3}'.format(out, m.group(2), m.group(3), m.group(4))
        return getattr(model_instance, self.attname)
    
class PSCField(models.CharField):

    def __init__(self, *args, **kwargs):
        super(PSCField, self).__init__(max_length=6, *args, **kwargs)
        
    def formfield(self, **kwargs):
        defaults = {'regex':r'^\d{3} ?\d{2}$'}
        defaults.update(kwargs)
        defaults['widget'] = WidgetFactory().create(FieldsWidget, {'class': 'psc'}, kwargs.get('widget', None))
        return super(models.CharField, self).formfield(form_class=forms.RegexField, **defaults)
    
    def pre_save(self, model_instance, add):
        m = re.match(r'^(\d{3}) ?(\d{2})$', getattr(model_instance, self.attname))
        return '{0} {1}'.format(m.group(1), m.group(2))





class NumericIdField(models.CharField):
    
    def __init__(self, verbose_name=None, name=None, places=4, **kwargs):
        models.CharField.__init__(self, verbose_name, name ,max_length=16, **kwargs)
        self.places = places
        
    def formfield(self, **kwargs):
        defaults = {'regex':r'^\d{%s}$' % self.places,}
        defaults.update(kwargs)
        return super(models.CharField, self).formfield(form_class=forms.RegexField, **defaults)

class CharIdField(models.CharField):
    
    def __init__(self, verbose_name=None, name=None, places=4, **kwargs):
        models.CharField.__init__(self, verbose_name, name ,max_length=16, **kwargs)
        self.places = places
        
    def formfield(self, **kwargs):
        defaults = {'regex':r'^[\dA-Z]{%s}$' % self.places,}
        defaults.update(kwargs)
        return super(models.CharField, self).formfield(form_class=forms.RegexField, **defaults)
    

class DICField(models.CharField):
    
    def __init__(self, verbose_name=None, name=None, **kwargs):
        models.CharField.__init__(self, verbose_name, name ,max_length=11, **kwargs)
    
    def formfield(self, **kwargs):
        defaults = {'regex':r'^[A-Z]{2}\d{1,9}$'}
        defaults.update(kwargs)
        return super(models.CharField, self).formfield(form_class=forms.RegexField, **defaults)
    

class HtmlField(models.TextField):
   
    def formfield(self, **kwargs):
        kwargs['widget'] = HtmlWidget(attrs={'class': 'tinymce'})
        return super(HtmlField, self).formfield(**kwargs)     
  
class PageUrlField(models.CharField):
    def formfield(self, **kwargs):
        kwargs['widget'] = WidgetFactory().create(forms.TextInput, {'class': 'page-url'}, kwargs.get('widget', None))
        return super(PageUrlField, self).formfield(**kwargs)
          
class PageTitleField(models.CharField):
   
    def formfield(self, **kwargs):
        kwargs['widget'] = WidgetFactory().create(FieldsWidget, {'class': 'page-title'}, kwargs.get('widget', None))
        return super(PageTitleField, self).formfield(**kwargs)

class Hide(object):
    def __init__(self, field, hide_if_set=False):
        self.field = field
        self.hide_if_set = hide_if_set
        
class HideCharField(models.CharField):
    
    def __init__(self, verbose_name=None, hide_relations=None, **kwargs):
        super(HideCharField, self).__init__(verbose_name, **kwargs)
        self.hide_relations = hide_relations
        
    def formfield(self, **kwargs):
        if (self.hide_relations):
            kwargs['widget'] = HideSelectWidget(hide_relations=self.hide_relations)
        return super(HideCharField, self).formfield(**kwargs)


class HideBooelanField(models.BooleanField):
    
    def __init__(self, verbose_name=None, hide=None, hide_if_checked=False, **kwargs):
        super(HideBooelanField, self).__init__(verbose_name, **kwargs)
        self.hide = hide
        self.hide_if_checked = hide_if_checked
        
    def formfield(self, **kwargs):
        class_name = 'hide unchecked'
        if (self.hide_if_checked):
            class_name = 'hide checked'
        
        if (self.hide):
            kwargs['widget'] = WidgetFactory().create(forms.CheckboxInput, {'class': '%s-%s' % (class_name, self.hide)}, kwargs.get('widget', None))
        return super(HideBooelanField, self).formfield(**kwargs)
   
class GoogleMapUrlField(models.URLField):

    def __init__(self, verbose_name=None, name=None, verify_exists=True, **kwargs):
        kwargs['max_length'] = kwargs.get('max_length', 500)
        models.CharField.__init__(self, verbose_name, name, **kwargs)
        self.validators.append(validators.URLValidator(verify_exists=verify_exists))
        
    def formfield(self, **kwargs):
        return super(GoogleMapUrlField, self).formfield(form_class=GoogleMapUrlFormField, **kwargs)

class ResizableFieldFile(FieldFile):
    
    def save(self, name, content, save=True):
        super(ResizableFieldFile, self).save(name, content, save)
        fit(self.path, settings.MAX_WIDTH, settings.MAX_HEIGHT)

        
class ResizableImageField(ImageField):
    attr_class = ResizableFieldFile
    
class SelectDateField(models.DateField):

    def formfield(self, **kwargs):
        year = date.today().year - 10
        kwargs['widget'] = SelectMonthYearWidget(years=range(year, year+20))
        return super(SelectDateField, self).formfield(form_class=forms.DateField, **kwargs)
    
class OrderField(models.PositiveIntegerField):
   
    def formfield(self, **kwargs):
        kwargs['widget'] = OrderWidget()
        return super(OrderField, self).formfield(**kwargs)        


class FullSizeManyToManyField(models.ManyToManyField):
    def formfield(self, **kwargs):
        defaults = {
            'form_class': FullSizeModelMultipleChoiceField,
        }
        defaults.update(kwargs)
        return super(FullSizeManyToManyField, self).formfield(**defaults)
   
class OtherCharField(models.CharField):
    
    def __init__(self, verbose_name=None, name=None, choices=None, other_label=_(u'Other'), hide_relations=None, **kwargs):
        super(OtherCharField, self).__init__(verbose_name, name,  **kwargs)
        self.other_choices = choices
        self.other_label = other_label
        self.hide_relations = hide_relations
        
    def formfield(self, **kwargs):
        defaults = {
            'choices': self.other_choices,
            'other_label': self.other_label,
            'hide_relations': self.hide_relations
        }
        defaults.update(kwargs)
        t =  super(OtherCharField, self).formfield(form_class=OtherSelectField, **defaults)
        return t
    
    '''
    Z důvodu get_FOO_display, původně jsem chtěl udělat pomocí přepsání formfield a nastavení choices ale to bych musel přepsat i validaci a celou metodu formfield
    '''
    def contribute_to_class(self, cls, name):
        self.set_attributes_from_name(name)
        self.model = cls
        cls._meta.add_field(self)
        if self.other_choices:
            setattr(cls, 'get_%s_display' % self.name, curry(cls._get_FIELD_display, field=self))
            
    def _get_flatchoices(self):
        flat = []
        for choice, value in self.other_choices:
            if isinstance(value, (list, tuple)):
                flat.extend(value)
            else:
                flat.append((choice,value))
        return flat
    flatchoices = property(_get_flatchoices)
    
class TreeForeignKey(models.ForeignKey):
    
    default_error_messages = {
        'invalid': _('Model %(model)s with pk %(pk)r does not exist.'),
        'tree-invalid': _('Can not select an object that causes the cycle.')
    }
    
    def __init__(self, to, parent=None, **kwargs):
        super(TreeForeignKey, self).__init__(to, **kwargs)
        self.parent = parent
        
    def formfield(self, **kwargs):
        db = kwargs.pop('using', None)
        defaults = {
            'form_class': TreeModelChoiceField,
            'queryset': self.rel.to._default_manager.using(db).complex_filter(self.rel.limit_choices_to),
            'to_field_name': self.rel.field_name,
            'parent': self.parent or self.name
        }
        defaults.update(kwargs)
        return super(models.ForeignKey, self).formfield(**defaults)
    
    def validate(self, value, model_instance):
        super(TreeForeignKey, self).validate(value, model_instance)
        if (value != None):
            obj = self.rel.to._default_manager.get(**{self.rel.field_name: value})
            while (obj != None):
                if (obj == model_instance):
                    raise exceptions.ValidationError(self.error_messages['tree-invalid'])
                obj = obj.parent
                
                
class OrderedForeignKey(models.ForeignKey):
    
    def __init__(self, to, order_by, **kwargs):
        super(OrderedForeignKey, self).__init__(to, **kwargs)
        self.order_by = order_by
        
    def get_choices(self, include_blank=True, blank_choice=BLANK_CHOICE_DASH):
        first_choice = include_blank and blank_choice or []
        if self.choices:
            return first_choice + list(self.choices)
        rel_model = self.rel.to
        if hasattr(self.rel, 'get_related_field'):
            lst = [(getattr(x, self.rel.get_related_field().attname), smart_unicode(x)) for x in rel_model._default_manager.complex_filter(self.rel.limit_choices_to).order_by(self.order_by)]
        else:
            lst = [(x._get_pk_val(), smart_unicode(x)) for x in rel_model._default_manager.complex_filter(self.rel.limit_choices_to)]
        return first_choice + lst
    
    
    def formfield(self, **kwargs):
        db = kwargs.pop('using', None)
        defaults = {'queryset': self.rel.to._default_manager.using(db).complex_filter(self.rel.limit_choices_to).order_by(self.order_by),}
        defaults.update(kwargs)
        return super(OrderedForeignKey, self).formfield(**defaults)