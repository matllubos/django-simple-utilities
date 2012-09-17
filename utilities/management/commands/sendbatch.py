from django.core.management.base import BaseCommand

from utilities.emails.mail_sender import MailSender

class Command(BaseCommand):
    args = ''
    help = 'Send the next batch of mass emails.'

    def handle(self, *args, **options):
        mail_sender = MailSender()
        self.stdout.write(mail_sender.send_batch()+"\n")