# coding: utf-8
import re
import unicodedata
import pickle
from types import UnicodeType

from django.contrib.admin.util import quote as django_quote
from django.utils.functional import lazy
from django.utils.safestring import mark_safe

def listToDict(aList):
    i = 0
    aDict = {}
    for a in aList:
        aDict[i] = a
        i+=1
    return aDict
    

import Image

def fit(file_path, max_width=None, max_height=None, save_as=None):
    # Open file
    img = Image.open(file_path)

    # Store original image width and height
    w, h = img.size

    # Replace width and height by the maximum values
    w = int(max_width or w)
    h = int(max_height or h)

    # Proportinally resize
    img.thumbnail((w, h), Image.ANTIALIAS)

    # Save in (optional) 'save_as' or in the original path
    img.save(save_as or file_path)

    return True


def remove_nonspacing_marks(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', unicode(s)) if unicodedata.category(c) != 'Mn')
    
def quote(url):
    url = django_quote(remove_nonspacing_marks(url))
    return re.sub(r' ', '-', url)

def strip_accents(s):
    return ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))


mark_safe_lazy = lazy(mark_safe, UnicodeType)




def get_referer(request, default=None):
    ''' 
    Return the referer view of the current request
    '''

    # if the user typed the url directly in the browser's address bar
    referer = request.META.get('HTTP_REFERER')
    if not referer:
        return default

    # remove the protocol and split the url at the slashes
    referer = re.sub('^https?:\/\/', '', referer).split('/')
    if referer[0] == request.META.get('SERVER_NAME'):
        return default

    # add the slash at the relative path's view and finished
    referer = '/'.join(referer)
    return referer



class MultiCookie():
    def __init__(self,cookie=None,values=None):
        if cookie != None:
            try:
                self.values = pickle.loads(cookie)
            except:
                self.values = None
        elif values != None:
            self.values = values
        else:
            self.values = None

    def __str__(self):
        return pickle.dumps(self.values)
