import re

from django import template
from django.contrib.humanize.templatetags.humanize import intcomma
from django.utils.encoding import force_unicode
from django.utils.formats import get_format


register = template.Library()

def localize(value):
    value = re.sub(",", get_format('THOUSAND_SEPARATOR'), value)
    return value

@register.filter  
def floatcomma(value):
    orig = force_unicode(value)
        
    integer_val, remain_val = re.split('[,\.]', orig)

    return '%s%s%s' % (localize(intcomma(integer_val)),  get_format('DECIMAL_SEPARATOR'), remain_val)
floatcomma.is_safe = True