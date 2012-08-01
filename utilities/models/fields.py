# coding: utf-8
import re

from datetime import date

from django.forms.util import flatatt
from django.db import models
from django.utils.encoding import smart_str
from django import forms
from django.db.models.fields import PositiveIntegerField
from django.utils.safestring import mark_safe
from django.utils.encoding import force_unicode
from django.contrib.admin import widgets 
from django.forms import extras
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core import validators     
from django.utils.translation import ugettext_lazy as _
from django.db.models.fields.files import FieldFile

from sorl.thumbnail import ImageField

from utilities.utils import fit

class FieldsWidget(forms.TextInput):
    class Media:
        js = (
              '%sutilities/js/jquery-1.6.4.min.js' % settings.STATIC_URL,
              '%sutilities/js/models/fields.js' % settings.STATIC_URL,
              )

class MeasureWidget(FieldsWidget):
    
    def __init__(self, attrs=None, measure=''):
        super(MeasureWidget, self).__init__(attrs=attrs)
        self.measure = measure
            
    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        
        final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
        if value != '':
            # Only add the 'value' attribute if a value is non-empty.
            final_attrs['value'] = force_unicode(self._format_value(value))
        return mark_safe(u'<input%s /> <strong>%s</strong>' % (flatatt(final_attrs),self.measure))

class HtmlWidget(forms.Textarea):
    class Media:
        js = (
              '%sutilities/js/models/tinymce/jscripts/tiny_mce/tiny_mce.js' % settings.STATIC_URL,
              '%sutilities/js/models/textareas.js' % settings.STATIC_URL,
              )
                
class WidgetFactory:
    
    def create(self, widget , attrs,  old_widget, **kwargs):
        
        try:
            if (old_widget):
                old_attrs = old_widget.attrs
            else:
                old_attrs = {}
        except AttributeError:
            old_attrs = {}
            
        for k, v in attrs.iteritems():
            try:
                old_attrs[k] += ' '+v
            except KeyError:
                old_attrs[k] = v
        
        return widget(attrs=old_attrs, **kwargs) 
    

class IntegerRangeField(models.IntegerField):
    
    def __init__(self, verbose_name=None, name=None, min_value=None, max_value=None, **kwargs):
        self.min_value, self.max_value = min_value, max_value
        models.IntegerField.__init__(self, verbose_name, name, **kwargs)
    
    def formfield(self, **kwargs):
        defaults = {'min_value': self.min_value, 'max_value':self.max_value}
        defaults.update(kwargs)
        return super(IntegerRangeField, self).formfield(**defaults)


class CommaWidget(forms.widgets.TextInput):
    def render(self, name, value, attrs=None):
        if (value):
            return super(CommaWidget, self).render(name, smart_str(value).replace('.', ','))
        return super(CommaWidget, self).render(name, value)


class CommaDecimalField(forms.FloatField):

    def clean(self, value):
        value = smart_str(value).replace(',', '.')
        return super(CommaDecimalField, self).clean(value)
       
class FloatRangeField(models.FloatField):
    def __init__(self, verbose_name=None, name=None, min_value=None, max_value=None, **kwargs):
        self.min_value, self.max_value = min_value, max_value
        models.FloatField.__init__(self, verbose_name, name, **kwargs)
    
    def formfield(self, **kwargs):
        kwargs['widget'] = CommaWidget(attrs={'class': 'integer'})
        defaults = {'min_value': self.min_value, 'max_value':self.max_value}
        defaults.update(kwargs)
        return super(FloatRangeField, self).formfield(form_class=CommaDecimalField, **defaults)


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
        if (self.format == 'CZ'):
            defaults = {'regex':r'^(\+?\d{3})? ?\d{3} ?\d{3} ?\d{3}$',}
        elif (self.format == 'DE'):
            defaults = {'regex':r'^(((((((00|\+)49[ \-/]?)|0)[1-9][0-9]{1,4})[ \-/]?)|((((00|\+)49\()|\(0)[1-9][0-9]{1,4}\)[ \-/]?))[0-9]{1,7}([ \-/]?[0-9]{1,5})?)$',} 
        elif (self.format == 'OPEN'):
            defaults = {'regex':r'^[\+\d\-\(\) ]+$',} 
        defaults['widget'] = WidgetFactory().create(FieldsWidget, {'class': '%s-phone' % self.format}, kwargs.get('widget', None))
        defaults.update(kwargs)
        return super(models.CharField, self).formfield(form_class=forms.RegexField, **defaults)
   
    def pre_save(self, model_instance, add):
        if (self.format == 'CZ' and model_instance.phone):
            m = re.match(r'^(\+?\d{3})? ?(\d{3}) ?(\d{3}) ?(\d{3})$', getattr(model_instance, self.attname))
            out = '+420'
            if (m.group(1)): out = '+'+re.sub(r'\+', '', m.group(1))
            return '{0} {1} {2} {3}'.format(out, m.group(2), m.group(3), m.group(4))
        return model_instance.phone

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
    
class DICField(models.CharField):
    
    def __init__(self, verbose_name=None, name=None, **kwargs):
        models.CharField.__init__(self, verbose_name, name ,max_length=11, **kwargs)
    
    def formfield(self, **kwargs):
        defaults = {'regex':r'^[A-Z]{2}\d{1,9}$'}
        defaults.update(kwargs)
        return super(models.CharField, self).formfield(form_class=forms.RegexField, **defaults)
    
class StylizedIntegerField(forms.IntegerField):
    
    def clean(self, value):
        value = smart_str(value).replace(' ', '')
        return super(StylizedIntegerField, self).clean(value)


class HtmlField(models.TextField):
   
    def formfield(self, **kwargs):
        kwargs['widget'] = HtmlWidget(attrs={'class': 'tinymce'})
        return super(HtmlField, self).formfield(**kwargs)
       
class StylizedPositiveIntegerField(PositiveIntegerField):
    
    def formfield(self, **kwargs):
        kwargs['widget'] = WidgetFactory().create(FieldsWidget, {'class': 'integer'}, kwargs.get('widget', None))
        return super(StylizedPositiveIntegerField, self).formfield(form_class=StylizedIntegerField, **kwargs)
    
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
        class_names = [];
        
        for key, hides in self.hide_relations.items():
            for hide in hides:
                class_name = 'set'
                if (hide.hide_if_set):
                    class_name = 'notset'
                class_names.append('%s-%s-%s' % (key, class_name, hide.field))
        if (class_names):
            kwargs['widget'] = WidgetFactory().create(forms.Select, {'class': 'select-hide '+(' '.join(class_names))}, kwargs.get('widget', None))
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
    
class IntegerMeasureField(IntegerRangeField):

    def __init__(self, verbose_name=None, name=None, min_value=None, max_value=None, measure=None, **kwargs):
        super(IntegerMeasureField, self).__init__(verbose_name, name, min_value, max_value, **kwargs)
        self.measure = measure
           
    def formfield(self, **kwargs):
        kwargs['widget'] = MeasureWidget(attrs={'class': 'integer'}, measure=self.measure)
        return super(IntegerMeasureField, self).formfield(**kwargs)

class PositiveIntegerMeasureField(PositiveIntegerField):

    def __init__(self, verbose_name=None, name=None, measure=None, **kwargs):
        super(PositiveIntegerMeasureField, self).__init__(verbose_name, name, **kwargs)
        self.measure = measure
           
    def formfield(self, **kwargs):
        kwargs['widget'] = MeasureWidget(attrs={'class': 'integer'}, measure=self.measure)
        return super(PositiveIntegerMeasureField, self).formfield(**kwargs)
    

class CommaMeasureWidget(MeasureWidget):
    
    def render(self, name, value, attrs=None):
        if (value):
            return super(CommaMeasureWidget, self).render(name, smart_str(value).replace('.', ','))
        return super(CommaMeasureWidget, self).render(name, value)
    
class FloatMeasureField(models.FloatField):

    def __init__(self, verbose_name=None, name=None, min_value=None, max_value=None, measure=None, **kwargs):
        super(FloatMeasureField, self).__init__(verbose_name, name,  **kwargs)
        self.min_value, self.max_value = min_value, max_value
        self.measure = measure
           
    def formfield(self, **kwargs):
        kwargs['widget'] = WidgetFactory().create(CommaMeasureWidget, {'class': 'float'}, kwargs.get('widget', None), **{'measure':self.measure})
        defaults = {'min_value': self.min_value, 'max_value':self.max_value}
        defaults.update(kwargs)
        return super(FloatMeasureField, self).formfield(form_class=CommaDecimalField, **defaults)

class GoogleMapURLFormField(forms.URLField):
    def clean(self, value):
        m = re.match(r"^.*src=\"([^\"]+)\".*$", value)
        if (m):
            value = m.group(1)
        if (not re.search(r"output\=embed", value)):
            value += '&amp;output=embed'

        if (not re.search(r"^https?://maps\.google\.cz/maps", value)):
            raise ValidationError(_(u'Toto není správné URL google map'))
        return super(GoogleMapURLFormField, self).clean(value)   

class GoogleMapUrlField(models.URLField):

    def __init__(self, verbose_name=None, name=None, verify_exists=True, **kwargs):
        kwargs['max_length'] = kwargs.get('max_length', 500)
        models.CharField.__init__(self, verbose_name, name, **kwargs)
        self.validators.append(validators.URLValidator(verify_exists=verify_exists))
        
    def formfield(self, **kwargs):
        return super(GoogleMapUrlField, self).formfield(form_class=GoogleMapURLFormField, **kwargs)

class ResizableFieldFile(FieldFile):
    
    def save(self, name, content, save=True):
        super(ResizableFieldFile, self).save(name, content, save)
        fit(self.path, settings.MAX_WIDTH, settings.MAX_HEIGHT)

        
class ResizableImageField(ImageField):
    
    attr_class = ResizableFieldFile
    

from django.utils.dates import MONTHS
from django.utils.safestring import mark_safe
from django.utils.formats import get_format
from django.conf import settings
from django.utils import datetime_safe
import datetime
import time

RE_DATE = re.compile(r'(\d{4})-(\d\d?)-(\d\d?)$')

def _parse_date_fmt():
    fmt = get_format('DATE_FORMAT')
    escaped = False
    output = []
    for char in fmt:
        if escaped:
            escaped = False
        elif char == '\\':
            escaped = True
        elif char in 'Yy':
            output.append('year')
            #if not self.first_select: self.first_select = 'year'
        elif char in 'bEFMmNn':
            output.append('month')
            #if not self.first_select: self.first_select = 'month'
        elif char in 'dj':
            output.append('day')
            #if not self.first_select: self.first_select = 'day'
    return output

class SelectMonthYearWidget(extras.SelectDateWidget):
    def render(self, name, value, attrs=None):
        try:
            year_val, month_val = value.year, value.month
        except AttributeError:
            year_val = month_val = None
            if isinstance(value, basestring):
                if settings.USE_L10N:
                    try:
                        input_format = get_format('DATE_INPUT_FORMATS')[0]
                        v = datetime.datetime(*(time.strptime(value, input_format)[0:6]))
                        year_val, month_val = v.year, v.month
                    except ValueError:
                        pass
                else:
                    match = RE_DATE.match(value)
                    if match:
                        year_val, month_val = [int(v) for v in match.groups()]
        choices = [(i, i) for i in self.years]
        year_html = self.create_select(name, self.year_field, value, year_val, choices)
        choices = MONTHS.items()
        month_html = self.create_select(name, self.month_field, value, month_val, choices)
        choices = [(i, i) for i in range(1, 32)]
    
        output = []
        for field in _parse_date_fmt():
            if field == 'year':
                output.append(year_html)
            elif field == 'month':
                output.append(month_html)
        return mark_safe(u'\n'.join(output))
    
    def value_from_datadict(self, data, files, name):
        y = data.get(self.year_field % name)
        m = data.get(self.month_field % name)
        d = 1
        if y == m == "0":
            return None
        if y and m and d:
            if settings.USE_L10N:
                input_format = get_format('DATE_INPUT_FORMATS')[0]
                try:
                    date_value = datetime.date(int(y), int(m), int(d))
                except ValueError:
                    return '%s-%s-%s' % (y, m, d)
                else:
                    date_value = datetime_safe.new_date(date_value)
                    return date_value.strftime(input_format)
            else:
                return '%s-%s-%s' % (y, m, d)
        return data.get(name, None)

class SelectDateField(models.DateField):

    def formfield(self, **kwargs):
        year = date.today().year - 10
        kwargs['widget'] = SelectMonthYearWidget(years=range(year, year+20))
        return super(SelectDateField, self).formfield(form_class=forms.DateField, **kwargs)
    
class OrderWidget(forms.TextInput):
    class Media:
        js = (
              '%sutilities/js/jquery-1.6.4.min.js' % settings.STATIC_URL,
              '%sutilities/js/order/jquery.ui.core.js' % settings.STATIC_URL,
              '%sutilities/js/order/jquery.ui.widget.js' % settings.STATIC_URL,
              '%sutilities/js/order/jquery.ui.mouse.js' % settings.STATIC_URL,
              '%sutilities/js/order/jquery.ui.sortable.js' % settings.STATIC_URL,
              '%sutilities/js/order/menu-sort.js' % settings.STATIC_URL,
            )

class OrderField(models.PositiveIntegerField):
   
    def formfield(self, **kwargs):
        kwargs['widget'] = OrderWidget()
        return super(OrderField, self).formfield(**kwargs)        


class FullSizeMultipleSelect(forms.SelectMultiple):
    def render(self, name, value, attrs={}, choices=()):
        attrs['size'] = '%s' % len(self.choices)
        if len(self.choices) < 5: 
            attrs['size'] = '5'
            
        return super(FullSizeMultipleSelect, self).render(name, value, attrs, choices)


class FullSizeModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    widget = FullSizeMultipleSelect

        
class FullSizeManyToManyField(models.ManyToManyField):
    def formfield(self, **kwargs):
        print 'Ted'
        defaults = {
            'form_class': FullSizeModelMultipleChoiceField,
        }
        defaults.update(kwargs)
        return super(FullSizeManyToManyField, self).formfield(**defaults)
       
        