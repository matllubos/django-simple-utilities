# coding: utf-8
import time

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db.models.signals import post_delete

from filters import *

class UserLanguageProfile(models.Model):
    user = models.OneToOneField(User)
    language = models.CharField(_('Language'), max_length=2, choices=settings.LANGUAGES)





class HtmlMail(models.Model):
    subject = models.CharField(_('Subject'), max_length=255, blank=False)
    html = models.TextField(_('Content'))
    sender = models.EmailField(_('Sender E-mail'))
    datetime = models.DateTimeField(_('Date and time'), auto_now=True)

    def __unicode__(self):
        datetime = time.strptime(str(self.datetime).split(".")[0], "%Y-%m-%d %H:%M:%S")
        return time.strftime("%H:%M:%S %d.%m.%Y", datetime)

class Recipient(models.Model):
    mail = models.EmailField(_('E-mail'))
    htmlmail = models.ForeignKey(HtmlMail)
    sent = models.BooleanField(_('Is sent'), default=False)

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

    def save(self, *args, **kwargs):
        if not self.pk:
            for obj in GeneratedFile.objects.filter(content_type=self.content_type).order_by('-datetime')[20:]:
                obj.delete()
        super(GeneratedFile, self).save(*args, **kwargs)


def remove_files(sender, instance, using, **kwargs):
    if instance.file:
        storage, path = instance.file.storage, instance.file.path
        storage.delete(path)

post_delete.connect(remove_files, sender=GeneratedFile)


class ParentProperty(object):

    def __init__(self, name, verbose_name=None):
        self.name = name
        self.short_description = name or verbose_name

    def __get__(self, obj, type=None):
        if obj and obj.pk:
            return getattr(obj.cast, self.name)


class TreeModelBase(models.Model):
    real_type = models.ForeignKey(ContentType, verbose_name=_(u'Type'), editable=False, null=False, blank=False)
    real_type.not_empty_related_filter = True

    def save(self, *args, **kwargs):
        if not self.pk:
            self.real_type = self._get_real_type()
        super(TreeModelBase, self).save(*args, **kwargs)

    def _get_real_type(self):
        return ContentType.objects.get_for_model(type(self))

    @property
    def cast(self):
        return self.real_type.get_object_for_this_type(pk=self.pk)

    class Meta:
        abstract = True
