import re
from datetime import date

from django import template
from django.contrib.humanize.templatetags.humanize import intcomma
from django.utils.encoding import force_unicode
from django.utils.formats import get_format
from django.template import defaultfilters


register = template.Library()


def localize(value):
    value = re.sub(",", get_format('THOUSAND_SEPARATOR'), value)
    return value


@register.filter
def floatcomma(value):
    orig = force_unicode(value)

    integer_val, remain_val = re.split('[,\.]', orig)

    return '%s%s%s' % (localize(intcomma(integer_val)), get_format('DECIMAL_SEPARATOR'), remain_val)
floatcomma.is_safe = True


@register.filter
def month_name(month_number):
    today = date.today()
    helper = date(today.year, int(month_number), 1)
    return defaultfilters.date(helper, 'F')
