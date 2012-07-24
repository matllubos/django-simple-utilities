# coding: utf-8
from django.db import models
from django.utils import translation

class I18nOrderManager(models.Manager):
        
    def get_query_set(self):
        qs = super(I18nOrderManager, self).get_query_set()
        if hasattr(self.model._meta, 'localized_ordering'):
            ordering_fields = []
            for field in self.model._meta.localized_ordering:
                ordering_fields.append('%s_%s' % (field, translation.get_language()))
            qs = qs.order_by(*ordering_fields)
            
        return qs
    
    def order_by(self, *args, **kwargs):
        return self.get_query_set().order_by(*args, **kwargs)
  
models.options.DEFAULT_NAMES += ('localized_ordering',)   
    
class I18nOrderBase(models.Model):
    
    objects = I18nOrderManager()

    class Meta:
        abstract = True
