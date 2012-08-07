from django.contrib.admin import widgets 
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse, NoReverseMatch
from django.conf import settings
from django.utils.translation import ugettext as _
from django.db.models.fields.related import ManyToOneRel

class UpdateRelatedFieldWidgetWrapper(widgets.RelatedFieldWidgetWrapper):
    

    def render(self, name, value, *args, **kwargs):
        rel_to = self.rel.to
        
        attrs = {}
        if (kwargs.has_key('attrs')):
            attrs = kwargs['attrs']
            
        if (attrs.has_key('class')):
            attrs['class'] += ' %s' % rel_to._meta.db_table
        else:
            attrs['class'] = rel_to._meta.db_table
        
        can_update_related = isinstance(self.rel, ManyToOneRel) and self.can_add_related
        
        info = (rel_to._meta.app_label, rel_to._meta.object_name.lower())

        
        try:
            related_url = reverse('admin:%s_%s_add' % info, current_app=self.admin_site.name)
        except NoReverseMatch:
            info = (self.admin_site.root_path, rel_to._meta.app_label, rel_to._meta.object_name.lower())
            related_url = '%s%s/%s/add/' % info


        if can_update_related:
            update_info = ('/admin/', rel_to._meta.app_label, rel_to._meta.object_name.lower(), value)
            update_related_url = '%s%s/%s/%s/' % update_info
            delete_related_url = '%s%s/%s/%s/delete' % update_info
            
        self.widget.choices = self.choices
        output = [self.widget.render(name, value, *args, **kwargs)]
        if self.can_add_related:
            # TODO: "id_" is hard-coded here. This should instead use the correct
            # API to determine the ID dynamically.
            output.append(u'<a href="%s" class="add-another" id="add_id_%s" onclick="return showAddAnotherPopup(this);"> ' % \
                (related_url, name))
            output.append(u'<img src="%simg/admin/icon_addlink.gif" width="10" height="10" alt="%s"/></a>' % (settings.ADMIN_MEDIA_PREFIX, _('Add Another')))
        
        if can_update_related:   
            output.append(u'<a href="%s" class="edit-another" id="edit_id_%s" onclick="return showEditAnotherPopup(this);"> ' % \
                (update_related_url, name))
            output.append(u'<img src="%simg/admin/selector-search.gif" width="10" height="10" alt="%s"/></a>' % (settings.ADMIN_MEDIA_PREFIX, _('Change')))
              
            output.append(u'<a href="%s" class="delete-another" id="delete_id_%s" onclick="return showDeleteAnotherPopup(this);"> ' % \
                (delete_related_url, name))
            output.append(u'<img src="%simg/admin/icon_deletelink.gif" width="10" height="10" alt="%s"/></a>' % (settings.ADMIN_MEDIA_PREFIX, _('Delete')))
            
            
        return mark_safe(u''.join(output))
    