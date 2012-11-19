import StringIO
import pickle

from celery import task
from django.db.models import get_model
from utilities.models import GeneratedFile
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from utilities.csv_generator import CsvGenerator
from django.utils import translation
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import admin


@task()
def generate_csv(generated_file_pk, app_label, model_name, ids, language):
    try:
        generated_file = GeneratedFile.objects.get(pk = generated_file_pk)
        admin.autodiscover()
        model = get_model(app_label, model_name)
        model_admin = admin.site._registry[model]

        
        translation.activate(language)
        model = get_model(app_label, model_name)
        queryset = model.objects.filter(pk__in = ids)    
        output = StringIO.StringIO()   
        csv_generator = CsvGenerator(model, model_admin.csv_fields, header=model_admin.csv_header, delimiter=model_admin.csv_delimiter, quotechar = model_admin.csv_quotechar,  DB_values = model_admin.csv_DB_values, csv_formatters=model_admin.csv_formatters, encoding=model_admin.csv_encoding)
        csv_generator.export_csv(output, queryset)
            
        generated_file.file.save('%s-%s.csv' % (model_name, generated_file.datetime), ContentFile(output.getvalue()))
        generated_file.save()
    
    except ObjectDoesNotExist:
        pass
    