# coding: utf-8
from django.db.models import Avg, Sum
from django.utils.datastructures import SortedDict
from django.db.models.fields import FieldDoesNotExist
from django.utils.safestring import mark_safe
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy as _

class DashboardFormatter(object):
    
    def __init__(self, field_name, title = None, measure = None):
        self.field_name = field_name
        self.title = title
        self.measure = measure
    
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
                
    def get_measure(self, model):
        if self.measure:
            return self.measure
        return ''
          
    def render(self, qs, admin):
        values = self.get_values(qs, admin)
        model = qs.model  
        return mark_safe(u'<th>%s:</th><td>%s %s</td>' % (force_unicode(self.get_title(model, admin)), force_unicode(values), force_unicode(self.get_measure(model))))
        
    def get_field_values(self, qs):
        return None
    
    def get_method_values(self, qs):
        return None
    
    def get_admin_method_values(self, qs, admin):
        return None
    
    def get_values(self, qs, admin):
        try: 
            qs.model._meta.get_field(self.field_name) 
            return self.get_field_values(qs)
        except FieldDoesNotExist: 
            try:
                return self.get_admin_method_values(qs, admin)
            except AttributeError:
                return self.get_method_values(qs)

class SumDashboardFormatter(DashboardFormatter):
     
    def get_field_values(self, qs):
        return qs.aggregate(Sum(self.field_name))["%s__sum" % self.field_name]
    
    def get_method_values(self, qs):
        values = 0
        for obj in qs:
            values += getattr(obj, self.field_name)()
        return values
      
    def get_admin_method_values(self, qs, admin):
        values = 0
        for obj in qs:
            values += getattr(admin, self.field_name)(obj)
        return values 
    
class AvgDashboardFormatter(DashboardFormatter):
     
    def get_field_values(self, qs):
        return qs.aggregate(Avg(self.field_name))["%s__avg" % self.field_name]
    
    def get_method_values(self, qs):
        values = 0
        if qs.count() > 0:
            for obj in qs:
                values += getattr(obj, self.field_name)()
            values /= qs.count()
        return values 
    
    def get_admin_method_values(self, qs, admin):
        values = 0
        if qs.count() > 0:
            for obj in qs:
                values += getattr(admin, self.field_name)(obj)
            values /= qs.count()
        return values 

class TableDashboardFormatter(DashboardFormatter):
     
    def __init__(self, field_name, other_title = _(u'Other'), *args, **kwargs):
        super(TableDashboardFormatter, self).__init__(field_name, *args, **kwargs)
        self.other_title = other_title
    
    def render(self, qs, admin):
        values = self.get_values(qs, admin)
        model = qs.model  
        rows = []      
        rows.append(u'<tr><th>%s</th><th></th></tr>' % self.get_title(model, admin))
        
        for key, value in values.items():
            rows.append(u'<tr><td>%s</td><td>%s %s</td></tr>' % (force_unicode(key), force_unicode(value), force_unicode(self.get_measure(model)))) 
        return mark_safe(u'<table>%s</table>' % u'\n'.join(rows))

 
    def get_field_values(self, qs):
        values = SortedDict()
        field = qs.model._meta.get_field(self.field_name) 
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
    
    def get_method_values(self, qs):
        values = SortedDict()
        for obj in qs:
            val = getattr(obj, self.field_name)()
            if (not val): val = self.other_title
            if (values.has_key(val)):
                values[val] += 1
            else:
                values[val] = 1
        return values 
    
    def get_admin_method_values(self, qs, admin):
        values = SortedDict()
        for obj in qs:
            val = getattr(admin, self.field_name)(obj)
            if (not val): val = self.other_title
            if (values.has_key(val)):
                values[val] += 1
            else:
                values[val] = 1
        return values 