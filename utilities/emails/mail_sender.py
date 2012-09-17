# coding: utf-8
import re

from datetime import datetime

from smtplib import SMTP

from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import translation

from utilities.models import  Recipient, Image, UserLanguageProfile, SiteEmail, HtmlMail
from django.utils.encoding import force_unicode

class MailSender:
    day_abbr = ((u'pondělí', u'úterý', u'středa', u'čtvrtek', u'pátek', u'sobota', u'neděle'))
    
    batch = 50
    
    
    def send_massmails(self, sbj, recips, template, context, images = []):
        html = render_to_string(template, context)
                
        htmlmail = HtmlMail()
        htmlmail.html = html
        htmlmail.subject = sbj
        htmlmail.save()
        
        for image in images:
            mail_image = Image()
            mail_image.htmlmail = htmlmail
            mail_image.image = image
            mail_image.save()
         
        for recip in recips:   
            recipient = Recipient()
            recipient.mail = recip
            recipient.htmlmail = htmlmail
            recipient.save()
        
        
    def send_mail(self, sbj, recip, template, context, sender=None, images = []):
        try:
            if (not sender):
                sender = SiteEmail.objects.get(pk = 1).mail
            html = render_to_string(template, context)
            self.htmlmail(force_unicode(sbj), recip, html, images, sender)
            return True
        except ObjectDoesNotExist:
            return False

        
    def send_admin_mail(self, sbj, template, context, perm= None, images = []):
        try:
            site_email = SiteEmail.objects.get(pk = 1)
            users = User.objects.all()
            if (perm):
                users = users.filter(Q(groups__permissions=perm) | Q(user_permissions=perm) ).distinct()
           
            
            lang = translation.get_language()
            for user in users:
                if (user.email):
                    try:
                        user_lang = UserLanguageProfile.objects.get(user=user).language
                        translation.activate(user_lang)
                    except ObjectDoesNotExist:
                        translation.activate(settings.LANGUAGE_CODE)
                        
                    self.htmlmail(force_unicode(sbj), user.email, render_to_string(template, context), images, site_email.mail)
            translation.activate(lang)
        except ObjectDoesNotExist:
            return False
    
    def addEmail(self, html, recip):
        return re.sub(r'\{ *mail *\}', recip, html)
        
    
    def htmlmail(self, sbj, recip, html, images, sender,charset='utf-8'):
        html = self.addEmail(html, recip)
        msgRoot = MIMEMultipart('related')
        msgRoot['Subject'] = sbj
        msgRoot['From'] = sender
        msgRoot['To'] =  recip
        msgRoot.preamble = 'This is a multi-part message in MIME format.'

        msgAlternative = MIMEMultipart('alternative')
        msgRoot.attach(msgAlternative)
   
        msgAlternative.attach(MIMEText(html, 'html', _charset=charset))

        for img in images:
            fp = open(settings.STATIC_ROOT+img[0], 'rb')
            msgImage = MIMEImage(fp.read())
            fp.close()
            msgImage.add_header('Content-ID', '<'+img[1]+'>')
            msgRoot.attach(msgImage)
        
        smtp = SMTP()
        smtp.connect('localhost')
        smtp.sendmail(sender, recip, msgRoot.as_string())
        smtp.quit()
    
    def send_batch(self):
        num_send_mails = 0
        htmlmails = HtmlMail.objects.filter(datetime__lte = datetime.now()).order_by('-datetime') 
        site_email = SiteEmail.objects.get(pk = 1) 
        out = []
        while (num_send_mails < self.batch):
            htmlmails = HtmlMail.objects.filter(datetime__lte = datetime.now()).order_by('-datetime') 
            if (not htmlmails.exists()):
                out.append("No mass emails to send.")
                break
            htmlmail = htmlmails[0]
            recipients = Recipient.objects.filter(htmlmail = htmlmail)
            html_images = Image.objects.filter(htmlmail = htmlmail)
            
            images = []
            j = 1
            for html_image in html_images:
                images.append([j, html_image.image])
                j += 1
            
            i = 0   
            for recipient in recipients:
                self.htmlmail(htmlmail.subject, recipient.mail, htmlmail.html, images, site_email.mail)
                recipient.delete()
                if (num_send_mails==self.batch): break
                num_send_mails += 1
                i += 1
                
            out.append(u"Send {0} emails with date {1}.".format(i, htmlmail))    
            recipients = Recipient.objects.filter(htmlmail = htmlmail)
            if (not recipients):
                out.append(u"Send all emails with date {0}.".format(htmlmail))
                htmlmail.delete()
                
            
        return '\n'.join(out)     
        
        
    