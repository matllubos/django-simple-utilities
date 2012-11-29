import re

from django.middleware.locale import LocaleMiddleware
from django.utils import translation
from django.conf import settings

from utilities.models import UserLanguageProfile
from django.core.exceptions import ObjectDoesNotExist

class AdminLocaleMiddleware(LocaleMiddleware):

    def process_request(self, request):
        if re.search(r'^/admin/', request.path):
            if hasattr(settings, 'BACKEND_LANGUAGE'):
                translation.activate(settings.BACKEND_LANGUAGE);
            else:
                super(AdminLocaleMiddleware, self).process_request(request)
            user = request.user
            if user.is_authenticated():
                try:
                    language_profile = UserLanguageProfile.objects.get(user=user)
                    language_profile.language = translation.get_language()
                except ObjectDoesNotExist:
                    language_profile = UserLanguageProfile(user=user, language=translation.get_language())
                language_profile.save()
        elif re.search(r'^/i18n/setlang/', request.path):
            super(AdminLocaleMiddleware, self).process_request(request)
        else:
            if hasattr(settings, 'FRONTEND_LANGUAGE'):
                translation.activate(settings.FRONTEND_LANGUAGE)
            else:
                super(AdminLocaleMiddleware, self).process_request(request)
                
        