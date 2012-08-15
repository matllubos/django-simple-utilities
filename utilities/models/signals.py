# coding: utf-8
from django.db import models
from django.template import defaultfilters
from django.utils.datastructures import SortedDict
from emails.mail_sender import MailSender
from django.conf import settings
from django.utils.translation import ugettext as _
from django.db.models.signals import post_save
from django.db.models.signals import post_syncdb
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission

def get_field_value(obj, field):
        val = getattr(obj, field.name)
        if field.choices: 
            val = obj._get_FIELD_display(field)
        if callable(val):
            val = val()
        
        if (field.get_internal_type() == "ManyToManyField"):
            val = u", ".join(m2mobj.__unicode__() for m2mobj in val.all())
        if (field.get_internal_type() == "DateTimeField"):
            return defaultfilters.date(val, "G:i j.n.Y")
        if (field.get_internal_type() == "DateField"):    
            return defaultfilters.date(val, "j.n.Y")
        if (field.get_internal_type() ==  "BooleanField"):
            if (val): val = u"Ano"
            else: val = u"Ne"
        return val


class DefaultPostSave(object):
    
    def pre_register(self, model, **kwargs):
        pass
        
    def register(self, model, **kwargs):
        self.pre_register(model, **kwargs)
        post_save.connect(self.action, sender=model)  

    def action(self, sender, instance, created, **kwargs):
        pass
    
class NotificationPostSave(DefaultPostSave):
    
    def pre_register(self, model, **kwargs):
        content_type = ContentType.objects.get_for_model(model)
        codename = 'can_receive_notification_%s' % content_type.model
        if not Permission.objects.filter(content_type=content_type, codename=codename):
        
            permission = Permission(name = 'Can receive notification', content_type = content_type, codename = codename)
            permission.save()
        
        codename = models.CharField(_('codename'), max_length=100)
    
    def action(self, sender, instance, created, **kwargs):
        if (created):
            mail_sender = MailSender()
            data = SortedDict()
            try:
                for notification_field in instance._meta.notification_fields:
                    field = instance._meta.get_field(notification_field)
                    data[field.verbose_name] =  get_field_value(instance, field)
            except AttributeError:
                pass
            context={'obj': instance,
                     'data': data, 
                     'obj_verbose_name':instance._meta.verbose_name, 
                     'obj_name': instance._meta.object_name, 
                     'obj_app_label':instance._meta.app_label, 
                     'SITE_URL':settings.SITE_URL
                     }
            content_type = ContentType.objects.get_for_model(instance)
            codename = 'can_receive_notification_%s' % content_type.model
            perm = Permission.objects.get(content_type=content_type, codename=codename)
            mail_sender.send_admin_mail(_(u'Nový záznam v administraci'), 'mail/admin/notification.html', context, perm=perm)

class SendCustomerNotificationPostSave(DefaultPostSave):
    
    models_data = {}
    
    def register(self, model, **kwargs):
        self.models_data[model._meta.db_table] = {'email_field': kwargs['email_field'], 'subject': kwargs['subject'], 'template': kwargs['template']}
        super(SendCustomerNotificationPostSave, self).register(model, **kwargs)

        
    def action(self, sender, instance, created, **kwargs):
        if (created):
            mail_sender = MailSender()
            recip = getattr(instance, self.models_data[instance._meta.db_table]['email_field'])
            context={'obj': instance,}
            mail_sender.send_mail(_(self.models_data[instance._meta.db_table]['subject']), recip, self.models_data[instance._meta.db_table]['template'], context)


send_notification = NotificationPostSave()
send_customer_notification = SendCustomerNotificationPostSave()