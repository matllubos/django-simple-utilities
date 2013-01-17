import cStringIO

from django.db.models import get_model
from django.core.files.base import ContentFile
from django.utils import translation
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import admin

from celery import task

from utilities.models import GeneratedFile
from utilities.csv_generator import CsvGenerator

@task()
def generate_csv(generated_file_pk, app_label, model_name, ids, csv_fields, language):
    try:
        generated_file = GeneratedFile.objects.get(pk = generated_file_pk)
        translation.activate(language)
        
        admin.autodiscover()
        model = get_model(app_label, model_name)
        model_admin = admin.site._registry[model]
        queryset = model.objects.filter(pk__in = ids) 
      
        output = cStringIO.StringIO() 
        csv_generator = CsvGenerator(model_admin, model, csv_fields, header=model_admin.csv_header, delimiter=model_admin.csv_delimiter, quotechar = model_admin.csv_quotechar,  DB_values = model_admin.csv_DB_values, csv_formatters=model_admin.csv_formatters, encoding=model_admin.csv_encoding)
        csv_generator.export_csv(output, queryset)
            
        generated_file.file.save('%s-%s.csv' % (model_name, generated_file.datetime), ContentFile(output.getvalue()))
        generated_file.save()
    
    except ObjectDoesNotExist:
        pass