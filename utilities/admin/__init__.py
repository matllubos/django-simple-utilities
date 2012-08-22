# coding: utf-8
from django.contrib import admin
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponse
from django.utils.html import escape, escapejs
from django import forms
from django.http import HttpResponseRedirect
from django.utils.encoding import force_unicode, smart_str
from django.contrib.admin.views.main import ChangeList
from django.contrib import messages
from django.db import transaction, router
from django.http import Http404
from django.core.exceptions import PermissionDenied
from django.contrib.admin.util import get_deleted_objects
from django.contrib.admin.util import unquote
from django.contrib.admin.options import csrf_protect_m
from django.template.defaultfilters import slugify

from utilities.deep_copy import deep_copy
from utilities.csv_generator import CsvGenerator

from widgets import UpdateRelatedFieldWidgetWrapper

def get_related_delete(deleted_objects):
    if not isinstance(deleted_objects, list):
        return [deleted_objects, ]
    out = []
    for url in deleted_objects:
        out.extend(get_related_delete(url))
    return out
    

class RelatedToolsAdmin(admin.ModelAdmin):
    delete_confirmation_template = 'admin/delete_confirmation.html'
    
    @csrf_protect_m
    @transaction.commit_on_success
    def delete_view(self, request, object_id, extra_context={}):
        if request.POST and "_popup" in request.POST:
            opts = self.model._meta

            obj = self.get_object(request, unquote(object_id))

            if not self.has_delete_permission(request, obj):
                raise PermissionDenied

            if obj is None:
                raise Http404(_('%(name)s object with primary key %(key)r does not exist.') % {'name': force_unicode(opts.verbose_name), 'key': escape(object_id)})

            using = router.db_for_write(self.model)

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

            return HttpResponse(u'<script type="text/javascript">opener.dismissDeletePopup(window, %s);</script>' % \
                                del_objects)
        
        extra_context['is_popup'] = "_popup" in request.REQUEST
        return super(RelatedToolsAdmin, self).delete_view(request, object_id, extra_context=extra_context)
            
        
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        if isinstance(db_field, (models.ForeignKey, models.ManyToManyField)):
            request = kwargs.pop("request", None)
            if db_field.__class__ in self.formfield_overrides:
                kwargs = dict(self.formfield_overrides[db_field.__class__], **kwargs)

            if isinstance(db_field, models.ForeignKey):
                formfield = self.formfield_for_foreignkey(db_field, request, **kwargs)
            elif isinstance(db_field, models.ManyToManyField):
                formfield = self.formfield_for_manytomany(db_field, request, **kwargs)


            if formfield and db_field.name not in self.raw_id_fields:
                related_modeladmin = self.admin_site._registry.get(
                                                            db_field.rel.to)
                can_add_related = bool(related_modeladmin and
                            related_modeladmin.has_add_permission(request))
                formfield.widget = UpdateRelatedFieldWidgetWrapper(
                            formfield.widget, db_field.rel, self.admin_site,
                            can_add_related=can_add_related)

            return formfield
        return super(RelatedToolsAdmin, self).formfield_for_dbfield(db_field, **kwargs)
    
    def response_change(self, request, obj):     
        if "_popup" in request.POST:
            pk_value = obj._get_pk_val()
            return HttpResponse('<script type="text/javascript">opener.dismissEditPopup(window, "%s", "%s");</script>' % \
                # escape() calls force_unicode.
                (escape(pk_value), escapejs(obj)))
        return super(RelatedToolsAdmin, self).response_change(request, obj)
        
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
        return forms.Media(js=js)
    media = property(_media)
        
class HiddenModelMixin(object):
    def get_model_perms(self, *args, **kwargs):
        perms = super(HiddenModelMixin, self).get_model_perms(*args, **kwargs)
        perms['list_hide'] = True
        return perms
 
 
class HiddenModelAdmin(HiddenModelMixin, RelatedToolsAdmin):
    pass

from django.contrib.admin.util import quote
 
class MarshallingChangeList(ChangeList):
    
    def url_for_result(self, result):
        return "../%s/%s/" % (getattr(result, self.model_admin.real_type_field).model, quote(getattr(result, self.pk_attname)))
       
 
class MarshallingAdmin(RelatedToolsAdmin):  
     
    real_type_field = 'real_type'
    parent = None
    childs = []
    change_form_template = 'admin/marshalling_change_form.html'
    change_list_template = 'admin/marshalling_change_list.html'
   
    def get_changelist(self, request, **kwargs):
        return MarshallingChangeList 
    
    def get_model_perms(self, *args, **kwargs):
        perms = super(MarshallingAdmin, self).get_model_perms(*args, **kwargs)
        if (self.parent != self.model):
            perms['list_hide'] = True
        perms['hide_add'] = True
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

    @csrf_protect_m
    @transaction.commit_on_success
    def delete_view(self, request, object_id, extra_context={}):
        if request.POST and not "_popup" in request.POST:
            opts = self.model._meta
            obj = self.get_object(request, unquote(object_id))
    
            if not self.has_delete_permission(request, obj):
                raise PermissionDenied
    
            if obj is None:
                raise Http404(_('%(name)s object with primary key %(key)r does not exist.') % {'name': force_unicode(opts.verbose_name), 'key': escape(object_id)})
    
            using = router.db_for_write(self.model)
            (deleted_objects, perms_needed, protected) = get_deleted_objects(
                [obj], opts, request.user, self.admin_site, using)


            if perms_needed:
                raise PermissionDenied
            obj_display = force_unicode(obj)
            self.log_deletion(request, obj, obj_display)
            self.delete_model(request, obj)

            self.message_user(request, _('The %(name)s "%(obj)s" was deleted successfully.') % {'name': force_unicode(opts.verbose_name), 'obj': force_unicode(obj_display)})

            if not self.has_change_permission(request, None):
                return HttpResponseRedirect("../../../../")
            return HttpResponseRedirect("../../../%s/" % self.parent.__name__.lower())
        return super(MarshallingAdmin, self).delete_view(request, object_id, extra_context=extra_context)
     
    def response_change(self, request, obj): 
        if "_save" in request.POST:
            opts = obj._meta
            verbose_name = opts.verbose_name
            msg = _('The %(name)s "%(obj)s" was changed successfully.') % {'name': force_unicode(verbose_name), 'obj': force_unicode(obj)}
            self.message_user(request, msg)
            if self.has_change_permission(request, None):
                return HttpResponseRedirect('../../%s' % self.parent.__name__.lower())
            else:
                return HttpResponseRedirect('../../../')
        return super(MarshallingAdmin, self).response_change(request, obj) 
            
    def response_add(self, request, obj, post_url_continue='../%s/'):
        if "_save" in request.POST:
            opts = obj._meta
            msg = _('The %(name)s "%(obj)s" was added successfully.') % {'name': force_unicode(opts.verbose_name), 'obj': force_unicode(obj)}
            self.message_user(request, msg)
            if self.has_change_permission(request, None):
                post_url = '../../%s' % self.parent.__name__.lower()
            else:
                post_url = '../../../'
            return HttpResponseRedirect(post_url)
        return super(MarshallingAdmin, self).response_add(request, obj, post_url_continue)  

    
class MultipleFilesImportMixin(object):
    change_form_template = 'admin/multiple_file_upload_change_form.html'
    
    def received_file(self, obj, file):
        pass

    def response_add(self, request, obj, post_url_continue='../%s/'):
        try:
            for file in request.FILES.getlist('files[]'):
                self.received_file(obj, file)
        except:
            messages.error(request, _(u'Cannot safe files.'))
            return HttpResponseRedirect('')
        
        return super(MultipleFilesImportMixin, self).response_add(request, obj, post_url_continue) 
        
    def response_change(self, request, obj):
        try:
            for file in request.FILES.getlist('files[]'):
                self.received_file(obj, file)
        except:
            messages.error(request, _(u'Cannot safe files.'))
            return HttpResponseRedirect('')
        
        return super(MultipleFilesImportMixin, self).response_change(request, obj) 

    def add_view(self, request, form_url='', extra_context={}):
        sup = super(MultipleFilesImportMixin, self)
        extra_context['multiplefilesimportmixin_super_template'] = sup.add_form_template or sup.change_form_template or 'admin/change_form.html'
        return sup.add_view(request, form_url, extra_context)
        
    def change_view(self, request, object_id, extra_context={}):
        sup = super(MultipleFilesImportMixin, self)
        extra_context['multiplefilesimportmixin_super_template'] = sup.change_form_template or 'admin/change_form.html'
        return sup.change_view(request, object_id, extra_context)
    
    
class CloneModelMixin(object):
    change_form_template = 'admin/clone_change_form.html'
        
    def pre_clone_save(self, obj):
        pass
        
    def response_change(self, request, obj):
        if ('_clone' in request.POST):
            opts = self.model._meta
            msg = _(u'The %(name)s "%(obj)s" was added successfully.') % {'name': force_unicode(opts.verbose_name), 'obj': force_unicode(obj)}
            copied_obj = deep_copy(obj, False)

            self.message_user(request, force_unicode(msg)+ " " + force_unicode(_(u'Please update another values')))
            if "_popup" in request.REQUEST:
                return HttpResponseRedirect(request.path + "../%s?_popup=1"% copied_obj.pk)
            else:
                return HttpResponseRedirect(request.path + "../%s" % copied_obj.pk)
        
        return super(CloneModelMixin, self).response_change(request, obj) 
    
    def add_view(self, request, form_url='', extra_context={}):
        sup = super(CloneModelMixin, self)
        extra_context['clonemodelmixin_super_template'] = sup.add_form_template or sup.change_form_template or 'admin/change_form.html'
        return sup.add_view(request, form_url, extra_context)
        
    def change_view(self, request, object_id, extra_context={}):
        sup = super(CloneModelMixin, self)
        extra_context['clonemodelmixin_super_template'] = sup.change_form_template or 'admin/change_form.html'
        return sup.change_view(request, object_id, extra_context)


class AdminPagingMixin(object): 
    change_form_template = 'admin/paging_change_form.html'
    page_ordering = 'pk'
    
    def add_view(self, request, form_url='', extra_context={}):
        sup = super(AdminPagingMixin, self)
        extra_context['pagingmixin_super_template'] = sup.add_form_template or sup.change_form_template or 'admin/change_form.html'
        return sup.add_view(request, form_url, extra_context)
        
    def change_view(self, request, object_id, extra_context={}):
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
        extra_context['pagingmixin_super_template'] = sup.change_form_template or 'admin/change_form.html'
        return sup.change_view(request, object_id, extra_context)
    

class TreeChangeList(ChangeList):
    
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
    
class TreeModelMixin(object):
    
    parent = None
    change_list_template = 'admin/change_tree.html'
    
    def queryset(self, request):
        qs = super(TreeModelMixin, self).queryset(request)
        
        for obj in qs:
            obj.depth = 0
        return qs
    
    def get_changelist(self, request, **kwargs):
        return TreeChangeList 

    def changelist_view(self, request, extra_context={}):
        sup = super(TreeModelMixin, self)
        extra_context['treemodelmixin_super_template'] = sup.change_list_template or 'admin/change_list.html'
        return sup.changelist_view(request, extra_context)

    
class CSVImportForm(forms.Form):
    csv_file = forms.FileField(max_length=50)
       

class CSVExportMixin(object):
    change_list_template = 'admin/csv_import_change_list.html'
    
    csv_delimiter = ';'
    csv_fields = ()
    csv_formatters = {}
    csv_quotechar = '"'
    csv_header = False
    csv_DB_values = False
    csv_bom = False
    csv_encoding = 'utf-8'
    
    actions = ['export_csv',]
    
    def pre_import_save(self, obj):
        pass
    
    def import_csv(self, f):
        csv_generator = CsvGenerator(self.model,self.csv_fields, header=self.csv_header, delimiter=self.csv_delimiter, quotechar = self.csv_quotechar, DB_values = self.csv_DB_values, csv_formatters=self.csv_formatters, encoding=self.csv_encoding)
        obj = csv_generator.import_csv(f, self)
        return obj

    def export_csv(self, request, queryset):
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=%s.csv' % slugify(queryset.model.__name__)
        if self.csv_bom:
            response.write("\xEF\xBB\xBF\n")
        csv_generator = CsvGenerator(self.model,self.csv_fields, header=self.csv_header, delimiter=self.csv_delimiter, quotechar = self.csv_quotechar, DB_values = self.csv_DB_values, csv_formatters=self.csv_formatters, encoding=self.csv_encoding)
        csv_generator.export_csv(response, queryset)
        return response
        
    export_csv.short_description = _(u"Exportovat do formátu CSV")
    
    def changelist_view(self, request, extra_context={}):
        sup = super(CSVExportMixin, self)  
        import_form = CSVImportForm()
        if ('_csv-import' in request.POST):
            import_form = CSVImportForm(request.POST, request.FILES)
            
            if(import_form.is_valid()):
                #try:
                self.import_csv(request.FILES['csv_file'])
                #    messages.info(request, _(u'CSV import byl úspěšně dokončen'))
                #except:
                #    messages.error(request, _(u'Špatný formát CSV souboru'))
            else:
                messages.error(request, _(u'File must be in CSV format.'))
            return HttpResponseRedirect('')
        extra_context['csvimportmixin_super_template'] = sup.change_list_template or 'admin/change_list.html'
        extra_context['import_form'] = import_form
        return sup.changelist_view(request, extra_context=extra_context)
    
class DashboardMixin(object):
    change_list_template = 'admin/dashboard_change_list.html'
    dashboard_table = []
    
    def changelist_view(self, request, extra_context={}):   
        sup = super(DashboardMixin, self)    
        dashboard_table = []       
        qs = self.queryset(request) 
        for row in self.dashboard_table:
            dashboard_table_row = []
            for col in row:
                dashboard_table_row.append(col.render(qs, self))
            dashboard_table.append(dashboard_table_row)    
            
        extra_context['dashboard_table'] = dashboard_table
        extra_context['dashboardmixin_super_template'] = sup.change_list_template or 'admin/change_list.html'
        return sup.changelist_view(request, extra_context=extra_context)
    