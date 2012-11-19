from datetime import datetime, timedelta

from django import template
from django.contrib.admin.templatetags.admin_list import result_hidden_fields, result_headers, results
from django.utils.safestring import mark_safe
from django.conf import settings
import os

register = template.Library()

@register.simple_tag
def file_image(generated_file, file_images, progress_image, error_image, timeout):
    if not generated_file.file:
        if is_error(generated_file, timeout):
            return error_image
        return progress_image
    
    
    file_name = generated_file.file.name
    file_type = file_name.split('.')[-1]
    return file_images.get(file_type.lower(), '%sutilities/images/icons/file.png' % settings.STATIC_URL)

@register.simple_tag
def filename(generated_file, timeout):
    if not generated_file.file:
        if is_error(generated_file, timeout):
            return 'error'
        return ''
    return os.path.basename(generated_file.file.name)

@register.filter                    
def sizify(value):
    """
    Simple kb/mb/gb size snippet for templates:
    
    {{ product.file.size|sizify }}
    """
    #value = ing(value)
    if value < 512000:
        value = value / 1024.0
        ext = 'kb'
    elif value < 4194304000:
        value = value / 1048576.0
        ext = 'mb'
    else:
        value = value / 1073741824.0
        ext = 'gb'
    return '%s %s' % (str(round(value, 2)), ext)


def is_error(generated_file, timeout):
    return datetime.now() - timedelta(seconds = timeout) > generated_file.datetime

@register.simple_tag 
def error_class(generated_file, timeout):
    if is_error(generated_file, timeout):
        return ' error' 
    return ''

@register.simple_tag 
def ready_class(generated_file):
    if datetime.now() - timedelta(seconds = 2) < generated_file.datetime:
        return ' ready' 
    return ''

