# coding: utf-8
from django.db.models import Avg, Sum
from django.utils.datastructures import SortedDict
from django.db.models.fields import FieldDoesNotExist
from django.utils.safestring import mark_safe
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy as _

from utilities.dashboard.widgets import TableDashboardWidget, DashboardWidget,\
    BarGraphDashboardWidget


class DashboardFormatter(object):
    
    widget = DashboardWidget
    
    def __init__(self, title, name, measure = None, colspan=1, widget=None):
        self.title = title
        self.measure = measure
        self.colspan = colspan
        widget = widget or self.widget
        if isinstance(widget, type):
            widget = widget()
        widget.colspan = colspan
        widget.name = name
        self.widget_instance = widget
        

    def get_title(self, model, admin):
        return self.title
    
    def get_colspan(self):
        return self.colspan
    
    def get_measure(self, model):
        if self.measure:
            return self.measure
        return ''
    
    def render(self, qs, admin):
        value = self.get_values(qs, admin)
        model = qs.model  
        return self.widget_instance.render(value, self.get_title(model, admin), self.get_measure(model))
      
    def get_values(self, qs, admin):
        return None
    
class FieldDashboardFormatter(DashboardFormatter):
    
    def __init__(self, field_name, title = None, measure = None, colspan = 1, widget = None, qs_filter=None):
        super(FieldDashboardFormatter, self).__init__(title, field_name , measure, colspan, widget)
        self.field_name = field_name
        self.qs_filter = qs_filter
    
    def get_title(self, model, admin):
        if self.title:
            return self.title
        else:
            try: 
                return model._meta.get_field(self.field_name).verbose_name
            except FieldDoesNotExist: 
                try:
                    return getattr(admin, self.field_name).short_description
                except AttributeError:
                    return getattr(model, self.field_name).short_description
                        
    def get_field_values(self, qs):
        return None
    
    def get_method_values(self, qs):
        return None
    
    def get_admin_method_values(self, qs, admin):
        return None
    
    def get_values(self, qs, admin):
        if (self.qs_filter):
            qs = qs.filter(**self.qs_filter)
        try: 
            qs.model._meta.get_field(self.field_name) 
            return self.get_field_values(qs)
        except FieldDoesNotExist: 
            try:
                return self.get_admin_method_values(qs, admin)
            except AttributeError:
                return self.get_method_values(qs)

class CountDashboardFormatter(DashboardFormatter):
    
    def __init__(self, title, colspan = 1):
        super(CountDashboardFormatter, self).__init__(title, 'objects-count', colspan=colspan)
        
    def get_values(self, qs, admin):
        return qs.count()
     
class SumDashboardFormatter(FieldDashboardFormatter):
     
    def get_field_values(self, qs):
        return round(qs.aggregate(Sum(self.field_name))["%s__sum" % self.field_name]  or 0, 2)
    
    def get_method_values(self, qs):
        values = 0
        for obj in qs:
            values += getattr(obj, self.field_name)()
        return round(values, 2)
      
    def get_admin_method_values(self, qs, admin):
        values = 0
        for obj in qs:
            values += getattr(admin, self.field_name)(obj)
        return round(values, 2)
    
class AvgDashboardFormatter(FieldDashboardFormatter):
     
    def get_field_values(self, qs):
        return round(qs.aggregate(Avg(self.field_name))["%s__avg" % self.field_name] or 0, 2)
    
    def get_method_values(self, qs):
        values = 0
        if qs.count() > 0:
            for obj in qs:
                values += getattr(obj, self.field_name)()
            values /= qs.count()
        return round(values, 2) 
    
    def get_admin_method_values(self, qs, admin):
        values = 0
        if qs.count() > 0:
            for obj in qs:
                values += getattr(admin, self.field_name)(obj)
            values /= qs.count()
        return round(values, 2)

class TableDashboardFormatter(FieldDashboardFormatter):
     
    widget = TableDashboardWidget
    
    def __init__(self, field_name, other_title = _(u'Other'), *args, **kwargs):
        super(TableDashboardFormatter, self).__init__(field_name, *args, **kwargs)
        self.other_title = other_title
     
    def get_field_values(self, qs):
        values = SortedDict()
        other = 0
        
        field = qs.model._meta.get_field(self.field_name) 
        if (field.choices):
            count = 0
            for choice in field.choices:
                num = qs.filter(**{field.name:choice[0]}).count()
                if (choice[0] != 'other'): values[choice[1]] = num
                count += num
            if (qs.count() != count): other = qs.count() - count
           
        elif (field.get_internal_type() == "ManyToManyField"):
            for obj in qs:
                for m2mobj in getattr(obj, field.name).all():
                    if (values.has_key(m2mobj.__unicode__())):
                        values[m2mobj.__unicode__()] += 1
                    else:
                        values[m2mobj.__unicode__()] = 1
                
        elif (field.get_internal_type() == "BooleanField"):
            values[force_unicode(_('Yes'))] = qs.filter(**{field.name: True}).count()
            values[force_unicode(_('No'))] = qs.filter(**{field.name: False}).count()
            
        elif (field.get_internal_type() == "OrderedForeignKey" or field.get_internal_type() == "ForeignKey" or field.get_internal_type() == "CharField"):
            for obj in qs:
                val = getattr(obj, field.name)
                if (not val): other += 1
                elif (values.has_key(val)):
                    values[val] += 1
                else:
                    values[val] = 1
        
        if other != 0:          
            values[self.other_title] = other
        return values
    
    def get_method_values(self, qs):
        values = SortedDict()
        other = 0
        for obj in qs:
            val = getattr(obj, self.field_name)()
            if (not val): other += 1
            elif (values.has_key(val)):
                values[val] += 1
            else:
                values[val] = 1
        
        if other != 0:          
            values[self.other_title] = other
        return values 
    
    def get_admin_method_values(self, qs, admin):
        values = SortedDict()
        other = 0
        for obj in qs:
            val = getattr(admin, self.field_name)(obj)
            if (not val): other += 1
            elif (values.has_key(val)):
                values[val] += 1
            else:
                values[val] = 1
        
        if other != 0:          
            values[self.other_title] = other
        return values 
    

        
    
class DaysDashboardFormatter(FieldDashboardFormatter):    
    widget = TableDashboardWidget
    days = [_('Sunday'), _('Monday'), _('Tuesday'), _('Wednesday'), _('Thursday'), _('Friday'), _('Saturday')]
    first_day = 1
    
    def get_field_values(self, qs):
        values = SortedDict()
        i = self.first_day
        while i < self.first_day + 7:
            values[force_unicode(self.days[(i % 7)])] = qs.filter(**{'%s__week_day' % self.field_name: (i % 7) + 1}).count()
            i+= 1
        return values
    
    def get_method_values(self, qs):
        values = SortedDict()
        i = self.first_day
        
        #firstly defined order
        while i < self.first_day + 7:
            values[force_unicode(self.days[(i % 7)])] = 0
        
        for obj in qs:
            val = getattr(obj, self.field_name)().isoweekday()
            if val == 7:
                val = 0

            day_name = force_unicode(self.days[val])
            values[day_name] += 1
            
        return values 
    
    def get_admin_method_values(self, qs, admin):       
        values = SortedDict()
        for obj in qs:
            val = getattr(admin, self.field_name)(obj).isoweekday()
            if val == 7:
                val = 0

            day_name = force_unicode(self.days[val])
            
            if (values.has_key(day_name)):
                values[day_name] += 1
            else:
                values[day_name] = 1
        return values 
    

class DayPartsDashboardFormatter(FieldDashboardFormatter):    
    widget = TableDashboardWidget
    
    def __init__(self, field_name, part_size = 3, *args, **kwargs):
        super(DayPartsDashboardFormatter, self).__init__(field_name, *args, **kwargs)
        self.part_size = part_size
    
    
    def get_parts(self):
        parts = []
        for i in range(0, 24, self.part_size):
            parts.append({'from': i, 'to':i+self.part_size})
        return parts
        
        
    def get_field_values(self, qs):
        values = SortedDict()
        parts = self.get_parts()
        for part in parts:
            part_name = '%sh - %sh' %(part['from'], part['to'])
            values[part_name] = 0
        
        for obj in qs:
            val = getattr(obj, self.field_name).hour
            
            for part in parts:
                if val >= part['from'] and val < part['to']:
                    part_name = '%sh - %sh' %(part['from'], part['to'])
                    values[part_name] += 1
                    
        return values
    
    def get_method_values(self, qs):
        values = SortedDict()
        parts = self.get_parts()
        for part in parts:
            part_name = '%sh - %sh' %(part['from'], part['to'])
            values[part_name] = 0
        for obj in qs:
            val = getattr(obj, self.field_name)().hour
            
            for part in parts:
                if val >= part['from'] and val < part['to']:
                    part_name = '%sh - %sh' %(part['from'], part['to'])
                    values[part_name] += 1

        return values 
    
    def get_admin_method_values(self, qs, admin):           
        values = SortedDict()
        parts = self.get_parts()
        for part in parts:
            part_name = '%sh - %sh' %(part['from'], part['to'])
            values[part_name] = 0
        for obj in qs:
            val = getattr(admin, self.field_name)(obj).hour
            
            for part in parts:
                if val >= part['from'] and val < part['to']:
                    part_name = '%sh - %sh' %(part['from'], part['to'])
                    values[part_name] += 1
                    
        return values 
    
    