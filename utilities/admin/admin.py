# coding: utf-8
from django.contrib import admin
from widgets import UpdateRelatedFieldWidgetWrapper
from django.db import models
from django.utils.translation import ugettext_lazy, ugettext as _
from django.http import HttpResponse
from django.utils.html import escape, escapejs
from django import forms
from django.http import HttpResponseRedirect
from django.utils.encoding import force_unicode, smart_str
from django.contrib.admin.views.main import ChangeList
from django.contrib import messages
from utilities.deep_copy import deep_copy
from django.views.decorators.csrf import csrf_protect
from django.db import transaction, router
from django.http import Http404
from django.core.exceptions import PermissionDenied
from django.contrib.admin.util import get_deleted_objects
from django.contrib.admin.util import unquote
from django.utils.decorators import method_decorator
from django.contrib.admin.options import csrf_protect_m
from django.views.generic.create_update import delete_object

def get_related_delete(deleted_objects):
    if not isinstance(deleted_objects, list):
        return [deleted_objects, ]
    out = []
    for url in deleted_objects:
        out.extend(get_related_delete(url))
    return out
    

class UpdateRelatedAdmin(admin.ModelAdmin):
    delete_confirmation_template = 'admin/delete_confirmation.html'
    
    @csrf_protect_m
    @transaction.commit_on_success
    def delete_view(self, request, object_id, extra_context={}):
        if request.POST and "_popup" in request.POST:
            opts = self.model._meta
            app_label = opts.app_label

            obj = self.get_object(request, unquote(object_id))

            if not self.has_delete_permission(request, obj):
                raise PermissionDenied

            if obj is None:
                raise Http404(_('%(name)s object with primary key %(key)r does not exist.') % {'name': force_unicode(opts.verbose_name), 'key': escape(object_id)})

            using = router.db_for_write(self.model)

        # Populate deleted_objects, a data structure of all related objects that
        # will also be deleted.
            (deleted_objects, perms_needed, protected) = get_deleted_objects(
            [obj], opts, request.user, self.admin_site, using)

            if perms_needed:
                raise PermissionDenied
            obj_display = force_unicode(obj)
            self.log_deletion(request, obj, obj_display)
            self.delete_model(request, obj)

            del_objects = []
            for url in get_related_delete(deleted_objects):
                url = unquote(url)
                import re
                m = re.match('.*href="/admin/([^/]*)/([^/]*)/([^/]*)/".*', unicode(url))
                del_objects.append({'app': smart_str(m.group(1)), 'model': smart_str(m.group(2)), 'id':smart_str(m.group(3))})

            pk_value = obj._get_pk_val()
            return HttpResponse(u'<script type="text/javascript">opener.dismissDeletePopup(window, %s);</script>' % \
                                del_objects)
        
        extra_context['is_popup'] = "_popup" in request.REQUEST
        return super(UpdateRelatedAdmin, self).delete_view(request, object_id, extra_context=extra_context)
            
        
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        """
        Hook for specifying the form Field instance for a given database Field
        instance.

        If kwargs are given, they're passed to the form Field's constructor.
        """
        request = kwargs.pop("request", None)

        # If the field specifies choices, we don't need to look for special
        # admin widgets - we just need to use a select widget of some kind.
        if db_field.choices:
            return self.formfield_for_choice_field(db_field, request, **kwargs)

        # ForeignKey or ManyToManyFields
        if isinstance(db_field, (models.ForeignKey, models.ManyToManyField)):
            # Combine the field kwargs with any options for formfield_overrides.
            # Make sure the passed in **kwargs override anything in
            # formfield_overrides because **kwargs is more specific, and should
            # always win.
            if db_field.__class__ in self.formfield_overrides:
                kwargs = dict(self.formfield_overrides[db_field.__class__], **kwargs)

            # Get the correct formfield.
            if isinstance(db_field, models.ForeignKey):
                formfield = self.formfield_for_foreignkey(db_field, request, **kwargs)
            elif isinstance(db_field, models.ManyToManyField):
                formfield = self.formfield_for_manytomany(db_field, request, **kwargs)

            # For non-raw_id fields, wrap the widget with a wrapper that adds
            # extra HTML -- the "add other" interface -- to the end of the
            # rendered output. formfield can be None if it came from a
            # OneToOneField with parent_link=True or a M2M intermediary.
            if formfield and db_field.name not in self.raw_id_fields:
                related_modeladmin = self.admin_site._registry.get(
                                                            db_field.rel.to)
                can_add_related = bool(related_modeladmin and
                            related_modeladmin.has_add_permission(request))
                formfield.widget = UpdateRelatedFieldWidgetWrapper(
                            formfield.widget, db_field.rel, self.admin_site,
                            can_add_related=can_add_related)

            return formfield

        # If we've got overrides for the formfield defined, use 'em. **kwargs
        # passed to formfield_for_dbfield override the defaults.
        for klass in db_field.__class__.mro():
            if klass in self.formfield_overrides:
                kwargs = dict(self.formfield_overrides[klass], **kwargs)
                return db_field.formfield(**kwargs)

        # For any other type of field, just call its formfield() method.
        return db_field.formfield(**kwargs)
    
    def response_change(self, request, obj):
        pk_value = obj._get_pk_val()
        
        if "_popup" in request.POST:
            return HttpResponse('<script type="text/javascript">opener.dismissEditPopup(window, "%s", "%s");</script>' % \
                # escape() calls force_unicode.
                (escape(pk_value), escapejs(obj)))
        else:
            return super(UpdateRelatedAdmin, self).response_change(request, obj)
        
    def _media(self):
        from django.conf import settings
            
        js = ['js/core.js', 'js/admin/RelatedObjectLookups.js',
                'js/jquery.min.js', 'js/jquery.init.js']
        if self.actions is not None:
            js.extend(['js/actions.min.js'])
        if self.prepopulated_fields:
            js.append('js/urlify.js')
            js.append('js/prepopulate.min.js')
        if self.opts.get_ordered_objects():
            js.extend(['js/getElementsBySelector.js', 'js/dom-drag.js' , 'js/admin/ordering.js'])
    
        
        js = ['%s%s' % (settings.ADMIN_MEDIA_PREFIX, url) for url in js]
        js.append('%sutilities/js/jquery-1.6.4.min.js' % settings.STATIC_URL)
        js.append('%sutilities/admin/js/RelatedObjectLookups.js' % settings.STATIC_URL)
        #.append('%sjs/admin/RelatedObjectLookups.js' % settings.STATIC_URL)
        return forms.Media(js=js)
    media = property(_media)
        
class HiddenModelAdmin(UpdateRelatedAdmin):
    def get_model_perms(self, *args, **kwargs):
        perms = admin.ModelAdmin.get_model_perms(self, *args, **kwargs)
        perms['list_hide'] = True
        return perms
 
from django.contrib.admin.util import quote
 
class MarshallingChangeList(ChangeList):
    
    def url_for_result(self, result):
        return "../%s/%s/" % (getattr(result, self.model_admin.real_type_field).model, quote(getattr(result, self.pk_attname)))
       
 
class MarshallingAdmin(UpdateRelatedAdmin):  
     
    real_type_field = 'real_type'
    parent = None
    childs = []
    change_form_template = 'admin/marshalling_change_form.html'
    change_list_template = 'admin/marshalling_change_list.html'
   
    def get_changelist(self, request, **kwargs):
        return MarshallingChangeList 
    
    def get_model_perms(self, *args, **kwargs):
        perms = admin.ModelAdmin.get_model_perms(self, *args, **kwargs)
        if (self.parent != self.model):
            perms['list_hide'] = True
        return perms
    
    def queryset(self, request, parent = False):
        if not parent:
            return super(MarshallingAdmin, self).queryset(request)
        qs = self.parent._default_manager.get_query_set()
        ordering = self.ordering or ()
        if ordering:
            qs = qs.order_by(*ordering)
        return qs
    
    def change_view(self, request, object_id, extra_context={}):
        from django.contrib.contenttypes.models import ContentType
        if object_id:
            obj = self.get_object(request, object_id)
            if ContentType.objects.get_for_model(type(obj)) != getattr(obj, self.real_type_field):
                return HttpResponseRedirect('../../%s/%s' % (getattr(obj, self.real_type_field).model, object_id))
            
        if self.parent:
            extra_context['parent'] = self.parent.__name__.lower()
            
        return super(MarshallingAdmin, self).change_view(request, object_id, extra_context=extra_context)
    
     
    def changelist_view(self, request, extra_context={}):
        if self.childs:
            childs = []
            for obj in self.childs:
                childs.append({'name': obj.__name__.lower(), 'verbose_name': obj._meta.verbose_name})
            extra_context['childs'] = childs
        return super(MarshallingAdmin, self).changelist_view(request, extra_context=extra_context)

    def response_change(self, request, obj):
        opts = obj._meta
        verbose_name = opts.verbose_name
        msg = _('The %(name)s "%(obj)s" was changed successfully.') % {'name': force_unicode(verbose_name), 'obj': force_unicode(obj)}
        
        if "_save" in request.POST:
            self.message_user(request, msg)
            # Figure out where to redirect. If the user has change permission,
            # redirect to the change-list page for this object. Otherwise,
            # redirect to the admin index.
            if self.has_change_permission(request, None):
                return HttpResponseRedirect('../../%s' % self.parent.__name__.lower())
            else:
                return HttpResponseRedirect('../../../')
        return super(MarshallingAdmin, self).response_change(request, obj) 
            
    def response_add(self, request, obj, post_url_continue='../%s/'):
        """
        Determines the HttpResponse for the add_view stage.
        """
        opts = obj._meta
        pk_value = obj._get_pk_val()

        msg = _('The %(name)s "%(obj)s" was added successfully.') % {'name': force_unicode(opts.verbose_name), 'obj': force_unicode(obj)}
        
        if "_save" in request.POST:
            self.message_user(request, msg)

            # Figure out where to redirect. If the user has change permission,
            # redirect to the change-list page for this object. Otherwise,
            # redirect to the admin index.
            if self.has_change_permission(request, None):
                post_url = '../../%s' % self.parent.__name__.lower()
            else:
                post_url = '../../../'
            return HttpResponseRedirect(post_url)
        return super(MarshallingAdmin, self).response_add(request, obj, post_url_continue)  
    
    
class MultipleFilesImport(UpdateRelatedAdmin):
    file_field = None
    
    def received_file(self, obj, file):
        pass

    def response_add(self, request, obj, post_url_continue='../%s/'):
        try:
            for file in request.FILES.getlist('files[]'):
                self.received_file(obj, file)
        except:
            messages.error(request, _(u'Nelze uložit soubory.'))
            return HttpResponseRedirect('')
        
        return super(MultipleFilesImport, self).response_add(request, obj, post_url_continue) 
    
        
    def response_change(self, request, obj):
        try:
            for file in request.FILES.getlist('files[]'):
                self.received_file(obj, file)
        except:
            messages.error(request, _(u'Nelze uložit soubory.'))
            return HttpResponseRedirect('')
        
        return super(MultipleFilesImport, self).response_change(request, obj) 
    
    change_form_template = 'admin/multiple_file_upload_change_form.html'
    
    
class CloneModelAdmin(UpdateRelatedAdmin):
    
    def pre_clone_save(self, obj):
        pass
        
    def response_change(self, request, obj):
        opts = self.model._meta
        msg = _('The %(name)s "%(obj)s" was added successfully.') % {'name': force_unicode(opts.verbose_name), 'obj': force_unicode(obj)}
        
        if ('_clone' in request.POST):
            copied_obj = deep_copy(obj, False)

            self.message_user(request, msg + " " + _(u"prosím upravte další hodnoty"))
            if "_popup" in request.REQUEST:
                return HttpResponseRedirect(request.path + "../%s?_popup=1"% copied_obj.pk)
            else:
                return HttpResponseRedirect(request.path + "../%s" % copied_obj.pk)
        
        return super(CloneModelAdmin, self).response_change(request, obj) 
    
    change_form_template = 'admin/clone_change_form.html'


class AdminPagingMixin(object): 
    
    change_form_template = 'admin/paging_change_form.html'
    page_ordering = 'pk'
    
    def add_view(self, request, form_url='', extra_context={}):
        sup = super(AdminPagingMixin, self)
        extra_context['prev_change_form_template'] = sup.change_form_template
        return sup.add_view(request, form_url, extra_context)
        
    def change_view(self, request, object_id, extra_context={}):
        #TODO: zdá se mi divné že extra_context už je předvyplněný
       
        sup = super(AdminPagingMixin, self)
        
        obj = sup.get_object(request, object_id)
        if hasattr(sup, 'parent'):
            qs = sup.queryset(request, True)
        else:
            qs = sup.queryset(request)
            
        qs = qs.order_by(self.page_ordering)
        next_qs = qs.filter(**{'%s__gt' % self.page_ordering:getattr(obj, self.page_ordering)}).order_by('%s' % self.page_ordering)
        prev_qs = qs.filter(**{'%s__lt' % self.page_ordering:getattr(obj, self.page_ordering)}).order_by('-%s' % self.page_ordering)
        
        if next_qs:
            extra_context['next_obj'] = {'app': next_qs[0]._meta.app_label, 'obj':next_qs[0]._meta.object_name.lower(), 'pk':next_qs[0]._get_pk_val(), 'verbose_name': next_qs[0]._meta.verbose_name}
        else:
            extra_context['next_obj'] = None
        if prev_qs:
            extra_context['prev_obj'] = {'app': prev_qs[0]._meta.app_label, 'obj':prev_qs[0]._meta.object_name.lower(), 'pk':prev_qs[0]._get_pk_val(), 'verbose_name': prev_qs[0]._meta.verbose_name}
        else:
            extra_context['prev_obj'] = None
        extra_context['prev_change_form_template'] = sup.change_form_template
        return sup.change_view(request, object_id, extra_context)
    

class ChangeTree(ChangeList):
    
    def tree_sort(self, parent):
        result = []
        ordering = self.model_admin.ordering
        filter_values = {self.model_admin.parent: parent}
        
        qs = self.result_list.filter(**filter_values)
        if (ordering):
            qs.order_by(ordering)
        for obj in qs:
            result = result + [obj.pk] + self.tree_sort(obj)
        return result
    
    def get_depth(self, obj):
        depth = 0
        parent =  getattr(obj, self.model_admin.parent)
        obj.parent
        while(parent != None):
            parent = getattr(parent, self.model_admin.parent)
            depth += 1
        return depth
    
class TreeModelAdmin(UpdateRelatedAdmin):
    
    parent = None
    change_list_template = 'admin/change_tree.html'
    
    def queryset(self, request):
        qs = super(TreeModelAdmin, self).queryset(request)
        
        for obj in qs:
            obj.depth = 0
        return qs
    
    def get_changelist(self, request, **kwargs):
        return ChangeTree 