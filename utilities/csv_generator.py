# coding: utf-8
import csv
from django.http import HttpResponse
from django.template.defaultfilters import slugify
from django.template import defaultfilters
from django.db.models.fields import FieldDoesNotExist
from django import forms
from django.contrib import admin 
from datetime import datetime
from django.utils import translation
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.conf import settings
from admin.admin import UpdateRelatedAdmin
import zipfile
import Image
from django.utils.translation import ugettext_lazy as _
from watermarker.utils import watermark
from watermarker import utils
from watermarker.models import Watermark

QUALITY = getattr(settings, 'WATERMARKING_QUALITY', 85)

class CSVError(Exception):
    """Base class for errors in this module."""
    pass

class ImportError(CSVError):
    def __init__(self, msg):
        Exception.__init__(self, msg)
        
        
class DefaultValue(object):
    
    def __init__(self, val, name = ''):
        self.val = val

    def get_val(self):
        return self.val
    
class NumberingValue(DefaultValue):
    def __init__(self, name = ''):
        super(NumberingValue, self).__init__(1, name=name)

    def get_val(self):
        val = self.val
        self.val +=1
        return val

class DefaultFormatter(object):
   
    def get_csv_field_value(self, obj, csv_field, DB_values):
        try: 
            field = obj._meta.get_field(csv_field)
            val = getattr(obj, field.name)
            if self.get_val(val):
                return self.get_val(val)
            
            if field.choices and not DB_values: 
                val = obj._get_FIELD_display(field)
            if callable(val):
                val = val()
            
            if (field.get_internal_type() == "ManyToManyField"):
                val = u", ".join(m2mobj.__unicode__() for m2mobj in val.all())
            if (field.get_internal_type() == "DateTimeField"):
                return defaultfilters.date(val, "G:i j.n.Y")
            if (field.get_internal_type() == "DateField"):    
                return defaultfilters.date(val, "j.n.Y")
            if (field.get_internal_type() ==  "BooleanField"):
                if (val): val = '1'
                else: val = '0'
            if (field.get_internal_type() ==  "TextField"):
                val = strip_tags(val)
            
            #TODO zatím odstraňuju, podle dokumentace tam nesmějí být
            if (val):
                val = unicode(val)
                val = re.sub(r'"', '', val)
            return val
        except FieldDoesNotExist:
            val = getattr(obj, csv_field)()
            if self.get_val(val):
                return self.get_val(val)
            return val
    
    def get_val(self, val):
        return None
    
    def set_db_val(self, obj, csv_field, csv_data):
        try: 
            field = obj._meta.get_field(csv_field)
            val = csv_data
            if (field.get_internal_type() ==  "BooleanField"):
                if (csv_data == '1'):
                    val = True
                elif (csv_data == '0' or csv_data == '' ):
                    val = False
                else:
                    raise ImportError('BooleanField can be only 0 or 1')
            
            elif (field.get_internal_type() ==  "ForeignKey"):
                raise ImportError('Cannot import ForeignKey object')
            
            elif (field.get_internal_type() in ['PositiveIntegerField', 'IntegerField']):
                if (val != ''):
                    val = int(val)
                else:
                    val = None
                
            elif (field.get_internal_type() == 'FloatField'):
                if (val != ''):
                    val = float(val)
                else:
                    val = None
            
            elif (field.get_internal_type() == "DateField"):    
                val = datetime.strptime(val, '%d.%m.%Y')
                    
            setattr(obj, csv_field, val)
        except FieldDoesNotExist:
            pass
     
    def pre_save(self, obj):
        pass
       
 
class DefaultModelFormatter(object):

    def __init__(self, model, csv_formatters = {}):
        self.model = model
        self.queryset = model.objects.all()
        self.csv_formatters = csv_formatters
        self.new_obj = model()
        self.object_formatters = []
        self.field_name = None
        
        
    def get_csv_field_value(self, obj, csv_field, DB_values):
        csv_field_parts = csv_field.split('.', 2)
        model_obj = getattr(obj, csv_field_parts[0])
        
        formatter = DefaultFormatter()
        
        if ('.' in csv_field_parts[1]):
            real_field_name = csv_field_parts[1].split('.', 2)[0]
            if (self.csv_formatters.has_key(real_field_name)):
                formatter = self.csv_formatters[real_field_name]
            
        elif (self.csv_formatters.has_key(csv_field_parts[1])):
            formatter = self.csv_formatters[csv_field_parts[1]]
                        
        val = formatter.get_csv_field_value(model_obj, csv_field_parts[1], DB_values)
        return val
        
    def set_db_val(self, obj, csv_field, csv_data): 
        csv_field_parts = csv_field.split('.', 2)
        self.field_name = csv_field_parts[0]
        
        formatter = DefaultFormatter()
        
        if ('.' in csv_field_parts[1]):
            real_field_name = csv_field_parts[1].split('.', 2)[0]
            if (self.csv_formatters.has_key(real_field_name)):
                formatter = self.csv_formatters[real_field_name]
                
        elif (self.csv_formatters.has_key(csv_field_parts[1])):
            formatter = self.csv_formatters[csv_field_parts[1]]
        
        formatter.set_db_val(self.new_obj, csv_field_parts[1], csv_data)
        self.object_formatters.append(formatter)
        
        filter_dict = {'%s' % re.sub(r'\.', '__', csv_field_parts[1]): csv_data}
        self.queryset = self.queryset.filter(**filter_dict)
        
    def pre_save(self, obj):
        if (self.queryset):
            setattr(obj, self.field_name, self.queryset[0])
        else:
            self.new_obj.save()
            setattr(obj, self.field_name, self.new_obj)
            
       
class MonthYearDateFormatter(DefaultFormatter):
    
    def get_val(self, val):
        return defaultfilters.date(val, "m.Y")
 
    def set_db_val(self, obj, csv_field, csv_data):
        if (csv_data != ''):
            val = datetime.strptime(csv_data, '1.%m.%Y')
            setattr(obj, csv_field, val)
        
         
class DateFormatter(DefaultFormatter):   
   
    def get_val(self, val):
        return defaultfilters.date(val, "d.m.Y")    
    
class CsvGenerator:
    
    def __init__(self, model,csv_fields, header = True, bom=True, delimiter=';',  quotation_marks = False, DB_values = False, csv_formatters = {}):
        self.header = header
        self.bom = bom
        self.quotation_marks = quotation_marks
        self.DB_values = DB_values
        self.csv_formatters = csv_formatters
        self.model = model
        self.delimiter = delimiter
        self.csv_fields = csv_fields
        
    def export_csv(self, output_stream, qs):
        writer = csv.writer(output_stream, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)
        # Write headers to CSV file
        
        fields = self.csv_fields
        
        headers = []
        
        '''
        if self.header:
            for field in fields:
                if (isinstance(field, DefaultValue)):
                    headers.append(field.name)
                elif (field):
                    try: 
                        headers.append(model._meta.get_field(field).verbose_name.encode('utf-8'))
                    except FieldDoesNotExist:
                        headers.append(getattr(model(), field).short_description.encode('utf-8'))
                else:
                    headers.append('""')

            writer.writerow(headers)

        
        for field in fields:
            headers.append(field)
        writer.writerow(headers)
        '''
        # Write data to CSV file
        for obj in qs:
            row = []
            for field in fields:
                if field in fields:
                    if (isinstance(field, DefaultValue)):
                        val = field.get_val()
                    elif (field):
                        formatter = DefaultFormatter()
                        
                        if ('.' in field):
                            real_field_name = field.split('.', 2)[0]
                            if (self.csv_formatters.has_key(real_field_name)):
                                formatter = self.csv_formatters[real_field_name]
                        elif (self.csv_formatters.has_key(field)):
                            formatter = self.csv_formatters[field]
                       
                       
                        val = formatter.get_csv_field_value(obj, field, self.DB_values)

                        if (not val):
                            val = ''
                        val = unicode(val).encode('iso-8859-15', 'ignore')
                    else:
                        val = ''
                  

                         
                    if self.quotation_marks:
                        val = '%s' % val

                    row.append(val)
                                    
            writer.writerow(row)
        # Return CSV file to browser as download
    
    #TODO: import s hlavičkou, nastavení oddělovače
    def import_csv(self, file, model_admin):
        rows = file.read().split("\"\r\n")
        
        objs = []
        for row in rows:

            
            if (re.search(r'^\s*$', row)):
                break
            
            if (len(rows) > 1):
                row = '%s"' % row
             
            
            columns = row.split(self.delimiter)
            if (len(columns) != len(self.csv_fields)):
                raise ImportError('Number of columns must be same as number csv_fields')
            i=0;
            obj = self.model()
            
            obj_formatters = []
            
            for field in self.csv_fields:
                
                val = re.sub(r'(^ *")|("\s*$)', '', columns[i])
                val = val.strip()
                
                
                if (isinstance(field, DefaultValue)):
                    if (val != unicode(field.val)):
                        raise ImportError('Value is not same as DefaultValue')
                elif (not field):
                    if (val != ''):
                        raise ImportError('None value must be empty')
                else:
                    formatter = DefaultFormatter()
                    if ('.' in field):
                        real_field_name = field.split('.', 2)[0]
                        if (self.csv_formatters.has_key(real_field_name)):
                            formatter = self.csv_formatters[real_field_name]
                    elif (self.csv_formatters.has_key(field)):
                        formatter = self.csv_formatters[field]
                        
                    formatter.set_db_val(obj, field, val)
                    obj_formatters.append(formatter)
                i+=1
            objs.append((obj, obj_formatters))
        
        for obj, formatters in objs:
            model_admin.pre_import_save(obj)
            for formatter in formatters:
                formatter.pre_save(obj)
            obj.save()
        return objs
    
 
import re
   
class CSVImportForm(forms.Form):
    csv_file = forms.FileField(max_length=50)
       

class CSVImportAdmin(UpdateRelatedAdmin):
    change_list_template = 'admin/csv_import_change_list.html'
    delimiter = ';'
    csv_fields = ()
    csv_formatters = {}
    csv_quotechar = '"'
    bom = False
    
    def pre_import_save(self, obj):
        pass
    
    def import_csv(self, f):
        csv_generator = CsvGenerator(self.model,self.csv_fields, header=False, bom=False, delimiter=self.delimiter, quotation_marks = True, DB_values = True, csv_formatters=self.csv_formatters)
        obj = csv_generator.import_csv(f, self)
        return obj

    def export_csv(self, request, queryset):
        
        translation.activate("de")
        
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=%s.csv' % slugify(queryset.model.__name__)
        if self.bom:
            response.write("\xEF\xBB\xBF\n")
        csv_generator = CsvGenerator(self.model, self.csv_fields, header=False, bom=False, delimiter=self.delimiter, quotation_marks = True, DB_values = True, csv_formatters=self.csv_formatters)
        csv_generator.export_csv(response, queryset)
        return response
        
    export_csv.short_description = _(u"Exportovat do formátu CSV")
    
    def changelist_view(self, request, extra_context={}):
        import_form = CSVImportForm()
        if ('_csv-import' in request.POST):
            import_form = CSVImportForm(request.POST, request.FILES)
            
            if(import_form.is_valid()):
                #try:
                self.import_csv(request.FILES['csv_file'])
                #    messages.info(request, _(u'CSV import byl úspěšně dokončen'))
                #except:
                #    messages.error(request, _(u'Špatný formát CSV souboru'))
            else:
                messages.error(request, _(u'Pro import je nutné vložit sobor ve formátu CSV'))
            return HttpResponseRedirect('')
        import_context = {
            'import_form': import_form,
        }
        
        extra_context.update(import_context)
        return super(CSVImportAdmin, self).changelist_view(request, extra_context=extra_context)
 
import cStringIO

def dirname(p):
    """Returns the directory component of a pathname"""
    i = p.rfind('/') + 1
    head = p[:i]
    if head and head != '/'*len(head):
        head = head.rstrip('/')
    return head

class VehicleCSVImportAdmin(CSVImportAdmin):   
    def export_zip_csv(self, request, queryset):
        """                                                                         
        Create a ZIP file on disk and transmit it in chunks of 8KB,                 
        without loading the whole file into memory. A similar approach can          
        be used for large dynamic PDF files.                                        
        """
        translation.activate("de")
        buffer = cStringIO.StringIO()
        archive = zipfile.ZipFile(buffer, 'w')
        
        temp = cStringIO.StringIO()
        
        csv_generator = CsvGenerator(self.model, self.csv_fields, header=False, bom=False, delimiter=self.delimiter, quotation_marks = True, DB_values = True, csv_formatters=self.csv_formatters)
        csv_generator.export_csv(temp, queryset)
        archive.writestr('car.csv',temp.getvalue())
        
        for car in queryset:
            i = 1
            for image in car.images.filter(export = True):
                
                try:
                    mark_watermark = Watermark.objects.get(name='Netautos', is_active=True)
                    target = Image.open(image.image.path)
                    mark = Image.open(mark_watermark.image.path)

                    wathermarked_image = watermark(target, mark, opacity=0.35, scale = utils.determine_scale('f', target, mark), position = utils.determine_position('c', target, mark), tile=1)
                    wathermarked_image_name = '%s_%s.jpg' % (car.id, i)
                    wathermarked_image_path = '%s/exported/%s' % (dirname(image.image.path), wathermarked_image_name)
                    wathermarked_image.save(wathermarked_image_path, quality=QUALITY)
                except Watermark.DoesNotExist:
                    wathermarked_image_path = image.image.path

                archive.write(wathermarked_image_path, '%s_%s.jpg' % (car.id, i), zipfile.ZIP_DEFLATED) 
                i += 1 
                if (i > 15):
                    break 

        archive.close()
        buffer.flush() 
        ret_zip = buffer.getvalue()
        buffer.close()
        response = HttpResponse(mimetype='application/zip')
        response['Content-Disposition'] = 'attachment; filename=export.zip'
        response.write(ret_zip)

        return response
    export_zip_csv.short_description = _(u"Exportovat do formátu CSV i s obrázky")
    
    
    def export_delete_images_csv(self, request, queryset):
        translation.activate("de")
        csv_fields = list(self.csv_fields)
        csv_fields[26] = DefaultValue('delete-images')
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=%s.csv' % slugify(queryset.model.__name__)
        if self.bom:
            response.write("\xEF\xBB\xBF\n")
        csv_generator = CsvGenerator(self.model, csv_fields, header=False, bom=False, delimiter=self.delimiter, quotation_marks = True, DB_values = True, csv_formatters=self.csv_formatters)
        csv_generator.export_csv(response, queryset)
        return response
    export_delete_images_csv.short_description = _(u"Exportovat do formátu CSV, který odstraní obrázky")    