#coding: utf-8
import time

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

class UserLanguageProfile(models.Model):
    user = models.OneToOneField(User)
    language = models.CharField(_('Language'), max_length=2, choices=settings.LANGUAGES)




    
class HtmlMail(models.Model):
    subject = models.CharField(_('Subject'), max_length=255, blank=False)
    html = models.TextField(_('Content'))
    datetime = models.DateTimeField(_('Date and time'), auto_now = True)
    
    def __unicode__(self):
        datetime = time.strptime(str(self.datetime).split(".")[0], "%Y-%m-%d %H:%M:%S")
        return time.strftime("%H:%M:%S %d.%m.%Y", datetime) 
    
class Recipient(models.Model):
    mail = models.EmailField(_('E-mail'))
    htmlmail = models.ForeignKey(HtmlMail)
    
    def __unicode__(self):
        return self.mail    
    
class Image(models.Model):
    htmlmail = models.ForeignKey(HtmlMail)
    image = models.CharField(_('File path'), max_length=100, blank=False)
    
    def __unicode__(self):
        return self.image    
    
class SiteEmail(models.Model):
    mail = models.EmailField('E-mail')
    
    def save(self):
        self.id = 1
        super(SiteEmail, self).save()

    def delete(self):
        pass
    
    def __unicode__(self):
        return self.mail   

    class Meta:
        verbose_name = 'E-mail webové stránky'
        verbose_name_plural = 'E-mail webové stránky'
        
        
        
        
# CSV Export



class GeneratedFile(models.Model):
    datetime = models.DateTimeField(_(u'Date and time of creation'), auto_now_add=True)
    content_type = models.ForeignKey(ContentType)
    file = models.FileField(_(u'Exported file'), upload_to="uploads/export/", null=True, blank=True)
    count_objects = models.PositiveIntegerField(_(u'Count objects'))
    