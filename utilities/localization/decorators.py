from django.contrib.admin.options import BaseModelAdmin
from django.db.models.base import ModelBase
from django.conf import settings

from easymode.i18n.admin import forms
from easymode.i18n.admin.generic import LocalizableGenericInlineFormSet
from easymode.utils.languagecode import get_all_language_codes, localize_fieldnames, get_real_fieldname
from easymode.i18n.admin.decorators import compute_prohibited, lazy_localized_list
from easymode.utils.languagecode import get_real_fieldname

def all_localize_fieldnames(fields, internationalized_fields):
    result = []   
    for field in fields:
        if field in internationalized_fields:
            for lang in settings.LANGUAGES:
                result.append(get_real_fieldname(field, lang[0]))
        else:
            result.append(field)    
    return result

class all_lazy_localized_list(lazy_localized_list):
   
    def __get__(self, obj, typ=None):
        return all_localize_fieldnames(self, self.localized_fieldnames)
    
__all__ = ('L10n', )

class L10n(object):
       
    error_no_model = "L10n: %s does not have model defined, but no model was passed to L10n either"
    
    def __new__(typ, model_or_admin=None, cls=None):
        """
        Construct object and if cls is passed as well apply the object to that 
        immediately. This makes this decorator a factory as well.
        """
        inline_syntax = True if cls is not None else False
        
        obj = object.__new__(typ)
        
        if isinstance(model_or_admin, ModelBase):
            # if model_or_admin is a model class set the model.
            obj.model = model_or_admin
        elif issubclass(model_or_admin, BaseModelAdmin):
            # if model_or_admin is an admin class, model MUST be defined on that class.
            if hasattr(model_or_admin, 'model'):
                obj.model = model_or_admin.model
                # set cls to the admin class
                cls = model_or_admin
            else:
                raise(AttributeError(L10n.error_no_model % model_or_admin.__name__))
        else:
            raise TypeError("L10n can not accept parameters of type %s" % model_or_admin.__name__)
        
        # when using inline syntax we need a new type, otherwise we could modify django's ModelAdmin!
        # inline_syntax is using L10n as: L10n(ModelAdmin, Model)
        if inline_syntax:
            descendant = type(obj.model.__name__ + cls.__name__, (cls,), {'model':obj.model})
            return obj.__call__(descendant)
        elif cls: # if cls is defined call __call__ to localize admin class.
            if not hasattr(cls, 'model'):
                assert hasattr(obj, 'model'), "obj 'always' has a model because it was assigned 10 lines ago."
                setattr(cls, 'model', obj.model)
            
            return obj.__call__(cls)
            
        return obj
    
    def __call__(self, cls):
        """run the filter on the class to be decorated"""
        if hasattr(cls, 'model'):
            self.model = cls.model
        elif not self.model:
            raise AttributeError(L10n.error_no_model % (cls.__name__) )

        # gather names of fields added by I18n
        added_fields = []
        for field in self.model.localized_fields:
            for language in get_all_language_codes():
                added_fields.append(get_real_fieldname(field, language))

        # determine name of the permission to edit untranslated fields
        permisson_name = "%s.can_edit_untranslated_fields_of_%s" % (
            self.model._meta.app_label, self.model.__name__.lower()
        )
        
        # make sure that fields become read_only when no permission is given.
        def get_readonly_fields(self, request, obj=None):
            if not request.user.has_perm(permisson_name):
                fields = self.fields or map(lambda x: x.name, self.model._meta.fields)
                # remove primary key because we don't show that, not even uneditable
                fields.pop(self.model._meta.pk_index())
                prohibited_fields = compute_prohibited(fields, self.exclude, self.model.localized_fields)
                
                return set(self.readonly_fields).union(prohibited_fields)
            
            return self.readonly_fields
        
        cls.get_readonly_fields = get_readonly_fields
        
        # override some views to hide fields which are not localized
        if hasattr(cls, 'change_view'):
            # BaseModelAdmin.__init__ will mess up our lazy lists if the following is
            # not allready defined
            if 'action_checkbox' not in cls.list_display and cls.actions is not None:
                cls.list_display = ['action_checkbox'] +  list(cls.list_display)
            
            if not cls.list_display_links:
                for name in cls.list_display:
                    if name != 'action_checkbox':
                        cls.list_display_links = [name]
                        break

            # Make certain properties lazy and internationalized
            cls.list_display_links = all_lazy_localized_list(cls.list_display_links, self.model.localized_fields)
            cls.list_display = all_lazy_localized_list(cls.list_display, self.model.localized_fields)
            cls.list_editable = all_lazy_localized_list(cls.list_editable, self.model.localized_fields)
            cls.search_fields = all_lazy_localized_list(cls.search_fields, self.model.localized_fields)
        
        return cls