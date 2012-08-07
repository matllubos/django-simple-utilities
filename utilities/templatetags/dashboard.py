# coding: utf-8
from django import template
from django.db.models import Avg, Sum
from django.utils.datastructures import SortedDict
from django.db.models.fields import FieldDoesNotExist
from django.contrib.auth.models import User, Group
from django.utils.safestring import mark_safe
from versions.models import TYPE
from django.core.exceptions import ObjectDoesNotExist
from datetime import timedelta
register = template.Library()

types ={ 
        'avg': u'průměr', 
        'sum': u'součet', 
        'table': ''
        }

class DashboardFormatter(object):
    
    def __init__(self, title = None, measure = None):
        self.title = title
        self.measure = None
    
    def get_title(self, model, field_name):
        if self.title:
            return self.title
        else:
            try: 
                return model._meta.get_field_by_name(field_name).verbose_name
            except FieldDoesNotExist: 
                return getattr(model, field_name).short_description
    
    def get_measure(self, model, field_name):
        if self.measure:
            return self.measure
        return ''
          
    def render(self, model, field_name, values):
        return mark_safe(u'<td>%s: %s %s</td>' % (self.get_title(model, field_name), values, self.get_measure(model, field_name)))
        
    def get_field_values(self, qs, field_name):
        return None
    
    def get_method_values(self, qs, field_name):
        return None
    
    def get_values(self, qs, field_name):
        try: 
            qs.model._meta.get_field_by_name(field_name) 
            return self.get_field_values(qs, field_name)
        except FieldDoesNotExist: 
            return self.get_method_values(qs, field_name)

class SumDashboardFormatter(DashboardFormatter):
     
    def get_field_values(self, qs, field_name):
        return qs.aggregate(Sum(field_name))["%s__sum" % field_name]
    
    def get_method_values(self, qs, field_name):
        values = 0
        for obj in qs:
            values += getattr(obj, field_name)()
        return values
       
    
class AvgDashboardFormatter(DashboardFormatter):
     
    def get_field_values(self, qs, field_name):
        return qs.aggregate(Avg(field_name))["%s__avg" % field_name]
    
    def get_method_values(self, qs, field_name):
        values = 0
        if qs.count() > 0:
            for obj in qs:
                values += getattr(obj, field_name)()
            values /= qs.count()
        return values 

class TableDashboardFormatter(DashboardFormatter):
     
    def __init__(self, other_title = _(u'Other'), *args, **kwargs):
        super(TableDashboardFormatter, self).__init__(*args, **kwargs)
        self.other_title = other_title
        
    def get_field_values(self, qs, field_name):
        values = SortedDict()
        field = qs.model._meta.get_field_by_name(field_name) 
        if (field.choices):
            count = 0
            for choice in field.choices:
                num = qs.filter(**{field.name:choice[0]}).count()
                if (choice[0] != 'other'): values[choice[1]] = num
                count += num
            if (qs.count() != count): values[self.other_title] = qs.count() - count
           
        elif (field.get_internal_type() == "ManyToManyField"):
            for obj in qs:
                for m2mobj in getattr(obj, field.name).all():
                    if (values.has_key(m2mobj.__unicode__())):
                        values[m2mobj.__unicode__()] += 1
                    else:
                        values[m2mobj.__unicode__()] = 1
                
        elif (field.get_internal_type() == "BooleanField"):
            values[_('Yes')] = qs.filter(**{field.name: True}).count()
            values[_('No')] = qs.filter(**{field.name: False}).count()
            
        elif (field.get_internal_type() == "ForeignKey" or field.get_internal_type() == "CharField"):
            for obj in qs:
                val = getattr(obj, field.name)
                if (not val): val = self.other_title
                if (values.has_key(val)):
                    values[val] += 1
                else:
                    values[val] = 1
        return values
    
    def get_method_values(self, qs, field_name):
        values = SortedDict()
        for obj in qs:
            val = getattr(obj, field_name)()
            if (not val): val = self.other_title
            if (values.has_key(val)):
                values[val] += 1
            else:
                values[val] = 1
        return values 



class DefaultDashboardFormatter(object):
    def getMethodValues(self, qs, field, other_title = "Jiná"):
        if (type == 'sum'):
            values = 0
            for obj in qs:
                values += getattr(obj, field)()
                    
            return self.return_values(values, qs)
        if (type == 'table'):
            values = SortedDict()
            for obj in qs:
                val = getattr(obj, field)()
                if (not val): val = other_title
                if (values.has_key(val)):
                    values[val] += 1
                else:
                    values[val] = 1
            return self.return_values(values, qs)
        return self.return_values(None, qs)
            
            
    def getFieldValues(self, qs, type, field, other_title = "Jiná"):
    
            if (type == 'avg'):
                if (field.get_internal_type() == "IntegerField" or field.get_internal_type() == "PositiveIntegerField"):
                    return self.return_values(qs.aggregate(Avg(field.name))["%s__avg" % field.name], qs)
            if (type == 'sum'):
                if (field.get_internal_type() == "IntegerField" or field.get_internal_type() == "PositiveIntegerField"):
                    return self.return_values(qs.aggregate(Sum(field.name))["%s__sum" % field.name], qs)
            if (type == 'table'):
                if (field.choices):
                    values = SortedDict()
                    count = 0
                    for choice in field.choices:
                        num = qs.filter(**{field.name:choice[0]}).count()
                        if (choice[0] != 'other'): values[choice[1]] = num
                        count += num
                    if (qs.count() != count): values[other_title] = qs.count() - count
                    return self.return_values(values, qs)
           
                if (field.get_internal_type() == "ManyToManyField"):
                    values = SortedDict()
                    for obj in qs:
                        val = getattr(obj, field.name)
                        for m2mobj in getattr(obj, field.name).all():
                            if (values.has_key(m2mobj.__unicode__())):
                                values[m2mobj.__unicode__()] += 1
                            else:
                                values[m2mobj.__unicode__()] = 1
                    return self.return_values(values, qs)
                if (field.get_internal_type() == "BooleanField"):
                    values = SortedDict()
                    values['Ano'] = qs.filter(**{field.name: True}).count()
                    values['Ne'] = qs.filter(**{field.name: False}).count()
                    return self.return_values(values, qs)
                if (field.get_internal_type() == "ForeignKey" or field.get_internal_type() == "CharField"):
                    values = SortedDict()
                    for obj in qs:
                        val = getattr(obj, field.name)
                        if (not val): val = other_title
                        if (values.has_key(val)):
                            values[val] += 1
                        else:
                            values[val] = 1
                    return self.return_values(values, qs)
            return self.return_values(None, qs)
    
    def return_values(self, values, qs):
        return values
    
   
def dashboard(qs):
    model = qs.model
    dashboard_fields = model._meta.dashboard_fields
    data = SortedDict()

    for dashboard_field in dashboard_fields:
        type = dashboard_field[0]
        field = dashboard_field[1]
        measure = None
        other_title = u'Jiná'
        if (len(dashboard_field) > 2 and dashboard_field[2]):
            measure = dashboard_field[2]
        if (len(dashboard_field) > 3 and dashboard_field[3]):
            other_title = dashboard_field[3]
        if (type == "count" and field == '__all__'):
            data[u"Počet položek"] = (qs.count(), measure)
        else:
            if (len(field.split('+')) ==2):
                first_field_name = field.split('+')[0]
                second_field_name  = field.split('+')[1]
            else:
                first_field_name  = field
                second_field_name = None
            formatter = DefaultDashboardFormatter()
            if (len(dashboard_field) > 4):
                formatter = dashboard_field[4]
            try:
                first_field = model._meta.get_field(first_field_name)
                second_field = None
                if (second_field_name):
                    second_field = model._meta.get_field(second_field_name)
                    
                value = formatter.getFieldValues(qs, type, first_field, second_field, other_title)
                data_key = first_field.verbose_name
                if (type != 'table'):
                    data_key = data_key+' - '+types.get(type)
                    
            except FieldDoesNotExist:
                value = formatter.getMethodValues(qs, type, first_field_name, second_field_name , other_title)
                data_key = getattr(qs.model(), first_field_name).short_description
            
            if (value):
                data[data_key] = (value, measure)
   

    return {'data':SortedDict(data)
           }
register.inclusion_tag('admin/block/dashboard.html')(dashboard)   
    
    
@register.simple_tag
def number(num):
    out = ''
    chars = list(str(int(num)))
    i = 1
    while len(chars) > 0:
        if (i % 4 == 0):
            out = ' '+out
        else:
            out = chars.pop()+out
        i += 1
    return out;