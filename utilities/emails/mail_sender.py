# coding: utf-8
import re

from datetime import datetime, timedelta

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
from django.core.mail import send_mass_mail

class MailSender:
    day_abbr = ((u'pondělí', u'úterý', u'středa', u'čtvrtek', u'pátek', u'sobota', u'neděle'))
    
    
    def send_massmails(self, sbj, recips, template, context, sender=None, images = []):
        try:
            if (not sender):
                sender = SiteEmail.objects.get(pk = 1).mail   
        except ObjectDoesNotExist:
            return False
        
        html = render_to_string(template, context)                
        htmlmail = HtmlMail.objects.create(
                                           html = html,
                                           subject = force_unicode(sbj),
                                           sender = sender
                                           )
        
        for image in images:
            Image.objects.create(
                                htmlmail = htmlmail,
                                image = image
                                )
         
        for recip in recips:   
            Recipient.objects.create(
                                    mail = recip,
                                    htmlmail = htmlmail
                                    )        
        return True;
        
    def send_mail(self, sbj, recip, template, context, sender=None, images = []):
        return self.send_massmails(sbj, [recip], template, context, sender, images)
        
    def send_admin_mail(self, sbj, template, context, perm=None, images = []):
        try:
            site_email = SiteEmail.objects.get(pk = 1)
            
            sent = False
            
            users = User.objects.filter(is_active=True, is_staff=True)
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
                    
                    sent = self.send_massmails(sbj, [user.email], template, context, site_email.mail, images)   

            translation.activate(lang)
            return sent
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
        
        self.smtp.sendmail(sender, recip, msgRoot.as_string())

    
    def connect(self):
        self.smtp = SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
        
        if settings.EMAIL_USE_TLS:
            self.smtp.ehlo()
            self.smtp.starttls()
            self.smtp.ehlo() 
        if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD :
            self.smtp.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    
    def quit(self):
        self.smtp.quit()
   
    
    def send_batch(self):
        num_send_mails = 0
        htmlmails = HtmlMail.objects.filter(datetime__lte = datetime.now(), pk__in = Recipient.objects.filter(sent = False).values('htmlmail')).order_by('-datetime') 
        out = []
        
        if (not htmlmails.exists()):
            out.append("No mass emails to send.")
        else:
            batch = settings.COUNT_MAILS_IN_BATCH
            self.connect()       
            
            i = 0
            while num_send_mails < batch and htmlmails.count() > i:
                htmlmail = htmlmails[i]
                recipients = Recipient.objects.filter(htmlmail = htmlmail, sent = False)
                
                html_images = Image.objects.filter(htmlmail = htmlmail)
            
                images = []
                j = 1
                for html_image in html_images:
                    images.append([j, html_image.image])
                    j += 1
                
                count_sent_mails = 0   
                for recipient in recipients:
                    self.htmlmail(htmlmail.subject, recipient.mail, htmlmail.html, images, htmlmail.sender)
                    recipient.sent = True
                    recipient.save()
                    if num_send_mails == batch: break
                    num_send_mails += 1
                    count_sent_mails += 1
                
                out.append(u"Send {0} emails with date {1}.".format(count_sent_mails, htmlmail))    
        
                
            self.quit()
            
        for old_mail in HtmlMail.objects.filter(datetime__lte = datetime.now() - timedelta(days=settings.COUNT_DAYS_TO_DELETE_MAIL)).exclude(pk__in = Recipient.objects.filter(sent = False).values('htmlmail')):
            old_mail.delete()
 
            
        return '\n'.join(out)     
        
        
    