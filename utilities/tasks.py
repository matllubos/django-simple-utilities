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


@task()
def generate_csv(generated_file_pk, app_label, model_name, ids, csv_fields, csv_header, csv_delimiter, csv_quotechar, csv_DB_values, csv_formatters, csv_encoding, language):
    try:
        generated_file = GeneratedFile.objects.get(pk = generated_file_pk)
        
        csv_fields = pickle.loads(csv_fields)
        csv_formatters = pickle.loads(csv_formatters)
        
        translation.activate(language)
        model = get_model(app_label, model_name)
        queryset = model.objects.filter(pk__in = ids)    
        output = StringIO.StringIO()   
        csv_generator = CsvGenerator(model, csv_fields, header=csv_header, delimiter=csv_delimiter, quotechar = csv_quotechar, DB_values = csv_DB_values, csv_formatters=csv_formatters, encoding=csv_encoding)
        csv_generator.export_csv(output, queryset)
            
        generated_file.file.save('%s-%s.csv' % (model_name, generated_file.datetime), ContentFile(output.getvalue()))
        generated_file.save()
    
    except ObjectDoesNotExist:
        pass
    