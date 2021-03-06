# coding: utf-8
import datetime
import re
import time
import inspect

from itertools import chain

from django import forms
from django.conf import settings
from django.utils.encoding import force_unicode, smart_str
from django.utils.safestring import mark_safe
from django.forms.util import flatatt
from django.utils.formats import get_format
from django.utils import datetime_safe
from django.utils.dates import MONTHS
from django.forms import extras
from django.utils.html import escape, conditional_escape

class WidgetFactory:
    def create(self, widget , attrs,  old_widget, **kwargs):
        try:
            if (old_widget):
                old_attrs = old_widget.attrs
            else:
                old_attrs = {}
        except AttributeError:
            old_attrs = {}
        
        if not old_widget or inspect.isclass(old_widget):                
            for k, v in attrs.iteritems():
                try:
                    values = ('%s %s' % (old_attrs[k], v)).split(' ')
                    old_attrs[k] = ' '.join(set(values))
                except KeyError:
                    old_attrs[k] = v
            return widget(attrs=old_attrs, **kwargs)
        elif isinstance(old_widget, widget):
            for k, v in kwargs.iteritems():
                try:
                    if not getattr(old_widget, k):
                        setattr(old_widget, k, v)
                except AttributeError:
                    setattr(old_widget, k, v)
                
            for k, v in attrs.iteritems():
                try:
                    values = ('%s %s' % (old_attrs[k], v)).split(' ')
                    old_attrs[k] = ' '.join(set(values))
                except KeyError:
                    old_attrs[k] = v
                
        
        return old_widget
    
    
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
        if self.measure:
            return mark_safe(u'<input%s /> %s' % (flatatt(final_attrs),self.measure))
        return mark_safe(u'<input%s />' % flatatt(final_attrs))

class CommaMeasureWidget(MeasureWidget):
    
    def render(self, name, value, attrs=None):
        if value:
            return super(CommaMeasureWidget, self).render(name, smart_str(value).replace('.', ','), attrs)
        return super(CommaMeasureWidget, self).render(name, value, attrs)
    
class HtmlWidget(forms.Textarea):
    class Media:
        js = (
              '%sutilities/js/models/tinymce/jscripts/tiny_mce/tiny_mce.js' % settings.STATIC_URL,
              '%sutilities/js/models/textareas.js' % settings.STATIC_URL,
              )

class CommaWidget(forms.widgets.TextInput):
    def render(self, name, value, attrs=None):
        if (value):
            return super(CommaWidget, self).render(name, smart_str(value).replace('.', ','))
        return super(CommaWidget, self).render(name, value)        
    
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

class ImmutableTextInput(forms.TextInput):
    
    def render(self, name, value, attrs={}):
        if value:
            attrs['readonly'] = 'readonly'
            attrs['class'] = 'readonly'
        return super(ImmutableTextInput, self).render(name, value, attrs)
    
    class Media:
        css = {
               'screen': ('%sutilities/css/models/fields.css' % settings.STATIC_URL,)
              }
class ImmutableSelect(forms.Select):
    
    def render_option(self, selected_choices, option_value, option_label):
        disabled_html = (not u'' in selected_choices and not option_value in selected_choices) and ' disabled="disabled"' or ''
        option_value = force_unicode(option_value)
        selected_html = (option_value in selected_choices) and u' selected="selected"' or ''
        return u'<option value="%s"%s%s>%s</option>' % (
            escape(option_value), selected_html, disabled_html,
            conditional_escape(force_unicode(option_label)))
    
    def render(self, name, value, attrs={}):
        if value:
            attrs['class'] = 'readonly'
        return super(ImmutableSelect, self).render(name, value, attrs)
    
    class Media:
        css = {
               'screen': ('%sutilities/css/models/fields.css' % settings.STATIC_URL,)
              }
               
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
        
class FullSizeMultipleSelectWidget(forms.SelectMultiple):
    def render(self, name, value, attrs={}, choices=()):
        attrs['size'] = '%s' % len(self.choices)
        if len(self.choices) < 5: 
            attrs['size'] = '5'
        return super(FullSizeMultipleSelectWidget, self).render(name, value, attrs, choices) 


class HideSelectWidget(forms.Select):        
    def __init__(self, attrs=None, choices=(), hide_relations=None):
        super(HideSelectWidget, self).__init__(attrs=attrs, choices=choices)
        self.hide_relations = hide_relations
    
    def render(self, name, value, attrs={}, choices=()):
        if self.hide_relations:
            class_names = [];
            for key, hides in self.hide_relations.items():
                for hide in hides:
                    class_name = 'set'
                    if (hide.hide_if_set):
                        class_name = 'notset'
                    class_names.append('%s--%s--%s' % (key.replace(' ', '__'), class_name, hide.field))
            if (class_names):
                if (attrs.has_key('class')):
                    attrs['class'] = '%s %s' % (attrs['class'], 'select-hide %s' % ' '.join(class_names))
                elif (self.attrs.has_key('class')):
                    attrs['class'] = '%s %s' % (self.attrs['class'], 'select-hide %s' % ' '.join(class_names))
                else:
                    attrs['class'] = 'select-hide %s' % ' '.join(class_names)
        return super(HideSelectWidget, self).render(name, value, attrs, choices)   
    
    class Media:
        js = (
              '%sutilities/js/jquery-1.6.4.min.js' % settings.STATIC_URL,
              '%sutilities/js/models/fields.js' % settings.STATIC_URL,
              )
        
        
class HideCheckboxWidget(forms.CheckboxInput):
    
    def __init__(self, attrs=None, hide_fields=None, *args, **kwargs):
        super(HideCheckboxWidget, self).__init__(attrs=attrs, *args, **kwargs)
        self.hide_fields = hide_fields
        
    def render(self, name, value, attrs={}):
        if self.hide_fields:
            class_names = [];
            for hide in self.hide_fields:
                class_name = 'checked'
                if (hide.hide_if_set):
                    class_name = 'unchecked'
                class_names.append('%s--%s' % (class_name, hide.field))
            if (class_names):
                if (attrs.has_key('class')):
                    attrs['class'] = '%s %s' % (attrs['class'], 'checkbox-hide %s' % ' '.join(class_names))
                elif (self.attrs.has_key('class')):
                    attrs['class'] = '%s %s' % (self.attrs['class'], 'checkbox-hide %s' % ' '.join(class_names))
                else:
                    attrs['class'] = 'checkbox-hide %s' % ' '.join(class_names)
        return super(HideCheckboxWidget, self).render(name, value, attrs)  
    
    class Media:
        js = (
              '%sutilities/js/jquery-1.6.4.min.js' % settings.STATIC_URL,
              '%sutilities/js/models/fields.js' % settings.STATIC_URL,
              )
    
        
class OtherSelectWidget(forms.widgets.MultiWidget):
    class Media:
        js = (
              '%sutilities/js/jquery-1.6.4.min.js' % settings.STATIC_URL,
              '%sutilities/js/models/fields.js' % settings.STATIC_URL,
              )
        
    def __init__(self, choices, other_label, hide_relations=None, attrs=None):
        choices_with_other = list(choices)
        choices_with_other.append((u'__other__', other_label))
        
        widgets = (
                   HideSelectWidget(choices = choices_with_other, attrs={'class':'other-select'}, hide_relations=hide_relations),
                   forms.TextInput(attrs={'class':'other-input'}),
       
        )
        
        super(OtherSelectWidget, self).__init__(widgets, attrs=attrs)
        self.choices = choices
        self.other_label = other_label
        
    def decompress(self, value):
        if value:
            if unicode(value) in [i[0] for i in self.choices]:
                return [value, None]
            else:
                return [u'__other__', value]
        return [None, None]
    
    def render(self, name, value, attrs=None):
        return super(OtherSelectWidget, self).render(name, value, attrs=attrs)
    
    
class MultipleOptgroupSelect(forms.Select):
        
    def render_group(self, selected_choices, option_value, option_label, depth):
        return u'<optgroup label="%s|- %s">%s</optgroup>' %('&nbsp;' * depth*2 ,conditional_escape(force_unicode(option_value)),''.join(self.process_list(selected_choices, option_label, depth + 1)))
    
    def render_option(self, selected_choices, option_value, option_label, depth):
        if option_value:
            depth -= 2
            if depth < 0:
                depth = 0
            
            option_value = force_unicode(option_value)
            selected_html = (option_value in selected_choices) and u' selected="selected"' or ''
            return u'<option value="%s"%s>%s|- %s</option>' % (
                escape(option_value), selected_html, '&nbsp;' * depth *2,
                conditional_escape(force_unicode(option_label)))
        return super(MultipleOptgroupSelect, self).render_option(selected_choices, option_value, option_label)
        
    def process_list(self, selected_choices,  l, depth=0):
        output = []
        for option_value, option_label in l:
            if isinstance(option_label, (list, tuple)):
                output.append(self.render_group(selected_choices, option_value, option_label, depth))
            else:
                output.append(self.render_option(selected_choices, option_value, option_label, depth))
        return output

    def render_options(self, choices, selected_choices):
        # Normalize to strings.
        selected_choices = set([force_unicode(v) for v in selected_choices])
        output = self.process_list(selected_choices, chain(self.choices, choices))
        return u'\n'.join(output)
