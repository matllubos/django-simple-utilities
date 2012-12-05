import django.db.models.options as options

print options.DEFAULT_NAMES
options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('admin_foreign_key_tools',)