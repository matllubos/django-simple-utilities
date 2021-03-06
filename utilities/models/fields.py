# coding: utf-8
import re

from datetime import date

from django.db import models
from django import forms
from django.db.models.fields import PositiveIntegerField, BLANK_CHOICE_DASH,\
    CharField
from django.core import validators, exceptions
from django.utils.translation import ugettext_lazy as _
from django.db.models.fields.files import FieldFile
from django.conf import settings
from django.utils.functional import curry

from sorl.thumbnail import ImageField as SorlImageField

from django.forms import Form
from utilities.utils import fit
from utilities.forms.widgets import WidgetFactory, FieldsWidget, HtmlWidget, MeasureWidget, SelectMonthYearWidget, OrderWidget,\
    HideSelectWidget, CommaMeasureWidget, HideCheckboxWidget, ImmutableTextInput, ImmutableSelect,\
    MultipleOptgroupSelect
   
from utilities import forms as utilities_forms
from utilities.utils import strip_accents

from django.utils.encoding import smart_unicode, force_unicode
from django.db.models.fields.subclassing import SubfieldBase
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.aggregates import Max


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
            defaults['form_class']= utilities_forms.AutoFormatIntegerField
         
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
            return super(FloatField, self).formfield(form_class=utilities_forms.CommaDecimalField, **defaults)
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
            form_class= utilities_forms.CzPhoneFormField
        elif (self.format == 'DE'):
            defaults = {'regex':r'^(((((((00|\+)49[ \-/]?)|0)[1-9][0-9]{1,4})[ \-/]?)|((((00|\+)49\()|\(0)[1-9][0-9]{1,4}\)[ \-/]?))[0-9]{1,7}([ \-/]?[0-9]{1,5})?)$',} 
        elif (self.format == 'OPEN'):
            defaults = {'regex':r'^[\+\d\-\(\)/ ]{6,50}$',} 
        
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
        value = getattr(model_instance, self.attname)
        m = re.match(r'^(\d{3}) ?(\d{2})$', value)
        if m:
            return '{0} {1}'.format(m.group(1), m.group(2))
        return value


class StrictEmailField(models.EmailField):

    def formfield(self, **kwargs):
        # As with CharField, this will cause email validation to be performed twice
        defaults = {
            'form_class': utilities_forms.StrictEmailField,
        }
        defaults.update(kwargs)
        return super(StrictEmailField, self).formfield(**defaults)

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
    
    def __init__(self, verbose_name=None, hide_fields=None, **kwargs):
        super(HideBooelanField, self).__init__(verbose_name, **kwargs)
        self.hide_fields = hide_fields
        
    def formfield(self, **kwargs):       
        if (self.hide_fields):
            kwargs['widget'] = HideCheckboxWidget(hide_fields=self.hide_fields)
        return super(HideBooelanField, self).formfield(**kwargs)
   
class GoogleMapUrlField(models.URLField):

    def __init__(self, verbose_name=None, name=None, verify_exists=True, **kwargs):
        kwargs['max_length'] = kwargs.get('max_length', 500)
        models.CharField.__init__(self, verbose_name, name, **kwargs)
        self.validators.append(validators.URLValidator(verify_exists=verify_exists))
        
    def formfield(self, **kwargs):
        return super(GoogleMapUrlField, self).formfield(form_class=utilities_forms.GoogleMapUrlField, **kwargs)



class GoogleSpreadsheet(object):
    
    def __init__(self, value):
        self.value = value
    
    @property
    def graph_hyperlink(self):
        return u'https://docs.google.com/spreadsheet/gform?key=%s&gridId=0#chart' % self.value
        
    @property
    def spreadsheet_hyperlink(self):
        return u'https://docs.google.com/spreadsheet/ccc?key=%s#gid=0' % self.value
    
    @property
    def form_hyperlink(self):
        return u'https://docs.google.com/spreadsheet/gform?key=%s&gridId=0#edit' % self.value

    def __unicode__(self):
        return "%s" % (self.value,)
    
    def __str__(self):
        return "%s" % (self.value,)
    
    def __len__(self):
        return len(self.value)

class GoogleSpreadsheetField(models.CharField):

    description = _(u"Google spreadsheet url")
    __metaclass__ = models.SubfieldBase
    
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 100
        super(GoogleSpreadsheetField, self).__init__(*args, **kwargs)

     
    def formfield(self, **kwargs):
        return super(GoogleSpreadsheetField, self).formfield(form_class=utilities_forms.GoogleSpreadsheetField, **kwargs)

    #Not working in SQKLite3
    def to_python(self, value):
        if isinstance(value, GoogleSpreadsheet):
            return value
        return GoogleSpreadsheet(value)


class ImageField(SorlImageField):

    def clean(self, value, model_instance):
        value.name = strip_accents(value.name)
        return super(ImageField, self).clean(value, model_instance)
    
class ResizableFieldFile(FieldFile):
    
    def save(self, name, content, save=True):
        super(ResizableFieldFile, self).save(name, content, save)
        fit(self.path, settings.MAX_WIDTH, settings.MAX_HEIGHT)

class ResizableImageField(ImageField):
    attr_class = ResizableFieldFile
    
class SelectDateField(models.DateField):

    def __init__(self, verbose_name=None, name=None, auto_now=False,
                 auto_now_add=False, from_year=None, to_year=None, 
                 from_year_increment=None, to_year_increment=None,
                 **kwargs):
        super(SelectDateField, self).__init__(verbose_name, name, auto_now, auto_now_add, **kwargs)
        self.from_year = date.today().year - 10
        self.to_year = date.today().year + 10

        if from_year_increment != None:
            self.from_year = date.today().year + from_year_increment
        
        if to_year_increment != None:
            self.to_year = date.today().year + to_year_increment
        
        if from_year != None:
            self.from_year = from_year
        if to_year != None:
            self.to_year = to_year


    def formfield(self, **kwargs):
        kwargs['widget'] = SelectMonthYearWidget(years=range(self.from_year, self.to_year + 1), required= not self.blank)
        return super(SelectDateField, self).formfield(form_class=forms.DateField, **kwargs)
 
#Renamed  
class DragAndDropInlineOrderField(models.PositiveIntegerField):
   
    def formfield(self, **kwargs):
        kwargs['widget'] = OrderWidget()
        return super(DragAndDropInlineOrderField, self).formfield(**kwargs)        
  
  
#In the future will be added ordering for diffrenet fields
class OrderField(models.PositiveIntegerField): 
     
    def __init__(self, *args, **kwargs):
        self.auto_add = kwargs.pop('auto_add', False)
        super(OrderField, self).__init__(*args,  **kwargs)
               
    def pre_save(self, model_instance, add):
        val =  super(OrderField, self).pre_save(model_instance, add)
        if val:
            qs = model_instance.__class__.objects.all()
            if not add:
                qs = qs.exclude(pk = model_instance.pk)
            try:
                obj = qs.get(**{self.name: val})

                setattr(obj, self.name, val + 1)
                obj.save()
            except ObjectDoesNotExist:
                pass
        elif self.auto_add:
            val = model_instance.__class__.objects.all().aggregate(Max('order'))['order__max'] 
            if not val:
                val = 0
            val += 1
        return val

    def formfield(self, **kwargs):
        defaults = {'min_value': 1}
        defaults.update(kwargs)
        return super(OrderField, self).formfield(**defaults)
        
        
class FullSizeManyToManyField(models.ManyToManyField):
    def formfield(self, **kwargs):
        defaults = {
            'form_class': utilities_forms.FullSizeModelMultipleChoiceField,
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
            'hide_relations': self.hide_relations,
        }
        defaults.update(kwargs)
        return super(OtherCharField, self).formfield(form_class=utilities_forms.OtherSelectField, **defaults)
    
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
            'form_class': utilities_forms.TreeModelChoiceField,
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
    
    
class GroupsForeignKey(models.ForeignKey):
    def __init__(self, to, group_by, order_by, **kwargs):
        super(GroupsForeignKey, self).__init__(to, **kwargs)
        self.group_by = group_by  
        self.order_by = order_by  
    
    def formfield(self, **kwargs):
        db = kwargs.pop('using', None)
        defaults = {
            'form_class': utilities_forms.GroupsModelChoiceField,
            'queryset': self.rel.to._default_manager.using(db).complex_filter(self.rel.limit_choices_to),
            'to_field_name': self.rel.field_name,
            'group_by': self.group_by,
            'order_by': self.order_by,
            'widget': MultipleOptgroupSelect
        }
        defaults.update(kwargs)
        return super(models.ForeignKey, self).formfield(**defaults)
    
#možná by v budoucnu bylo lepší přepsat celé fieldy a dát immutable=True/false   
class ImmutableCharField(models.CharField):
    def formfield(self, **kwargs):
        defaults = {}
        defaults.update(kwargs)
        defaults['widget'] = WidgetFactory().create(ImmutableTextInput, {}, kwargs.get('widget', None))
        return super(ImmutableCharField, self).formfield(**defaults)
    
class ImmutableForeignKey(models.ForeignKey):
    def formfield(self, **kwargs):
        defaults = {}
        defaults.update(kwargs)
        defaults['widget'] = WidgetFactory().create(ImmutableSelect, {}, kwargs.get('widget', None))
        return super(ImmutableForeignKey, self).formfield(**defaults)


class NullableCharField(models.CharField):
    description = "CharField that obeys null=True"
    
    def __init__(self, *args, **kwargs):
        super(NullableCharField, self).__init__(null=True, blank=True, *args,  **kwargs)

    def to_python(self, value):
        if isinstance(value, models.CharField):
            return value
        return value or ""

    def get_db_prep_value(self, value, *args, **kwargs):
        return value or None
     
    
class NonUTFFieldFile(models.FileField):
    
    def get_filename(self, filename):
        from unidecode import unidecode
        return super(NonUTFFieldFile, self).get_filename(unidecode(filename))
    
    
    