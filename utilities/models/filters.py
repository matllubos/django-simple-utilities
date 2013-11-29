# coding: utf-8
from django.contrib.admin.filterspecs import RelatedFilterSpec, FilterSpec, AllValuesFilterSpec
from django.utils.encoding import smart_unicode

class NotEmptyRelatedFilterSpec(RelatedFilterSpec):
    def __init__(self, f, request, params, model, model_admin,
                 field_path=None):
        super(NotEmptyRelatedFilterSpec, self).__init__(f, request, params, model, model_admin, field_path)
        self.lookup_choices = [(x._get_pk_val(), smart_unicode(x)) for x in set([getattr(obj, f.name) for obj in model._default_manager.all()])]

FilterSpec.filter_specs.insert(0, (lambda f: hasattr(f, 'not_empty_related_filter'), NotEmptyRelatedFilterSpec))