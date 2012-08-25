This project provides admin and model utilities which can save time during development, plus some utilities that simplify work with django administration.

Features:

	Administration
		* Update and delete button for foreignKey
		* Tree objects list
		* Simple CSV import as action
		* Multiple files upload
		* Clone button at admin form
	
	Model fields
		* Float field with comma
		* Integer field with min_value and max_value that can be set at model
		* Integer and float that will be displayed with measure
		* Czech Phone, PSC and DIC field with validation
		* Text field with TinyMce
		* Char field with choices that will be displayed as select box with the option to insert custom value
	
	
Instalation:
============

	You can use one of these commands::
		pip install django-simple-utilities
		easy_install django-simple-utilities

Configuration:
==============

Firstly you must add utilities to INSTALLED_APPS in settings.py before django.contrib.admin::

	INSTALLED_APPS = (
	    …
	    'utilities',
	    'django.contrib.admin',
	    …
	)

And finally run:: manage.py collectstatic


Usage:
======

Model fields:
-------------

django-simple-utilities adds some model fields which simplify your work. All this fields is in utilities.models.fields file. There is its list:
	
	* IntegerField:
		constructor: IntegerField(min_value=None, max_value=None, measure=None, auto_format=False, **kwargs)
		
			* min_value		- 	adds validation to min value
			* max_value		- 	adds validation to max value
			* measure		- 	you can add measure which will be display after input. For example if measure='EUR', generated input HTML will be:: <input ... /> EUR
			* auto_format 	- 	integer will be automatic formated using spaces for thousands. This feature use	JavaScript.
			
	* PositiveIntegerField:
		constructor: IntegerField(min_value=0, max_value=None, measure=None, auto_format=False, **kwargs)
		
		this is the same as IntegerField bud min_value must be higher than 0 and is set to 0 by default
		
	* FloatField:
		constructor: FloatField(min_value=0, max_value=None, measure=None, auto_format=False, comma=True, **kwargs)
		
			* comma	-	if comma is set to True input use comma without decimal point 
			* other values is same as IntegerField
		
	* PhoneField:
		constructor:  PhoneField(format='CZ', **kwargs):
			
			* format	-	has choices : CZ, DE, OPEN
			
		When you use CZ format is number automaticly formatted by JavaScript and user can insert only real cz phone number
		
			
	* PSCField:
		Czech PSC (For example 143 00), Input value is automaticly formated with JavaScript or after safe in field method clean.
		
		
	* DICField:
		Czech DIC		
		
		
	* HtmlField:
		This field uses text field and adds to textarea TinyMCE editor.
		
	* TreeForeignKey:
		constructor: TreeForeignKey(to, parent=None, **kwargs)
		
		This field is used for models which have tree structure. Result is select box which contains values with tree structure.
			
			* parent - 	field in string format which point to parent object. If parent is same as variable containing TreeForeignKey need not be set.
	
	* OrderedForeignKey:
		constructor:  OrderedForeignKey(to, order_by, **kwargs):	
			
			if you want set special different ordering in the final select box, you can use this field.

	* OtherCharField:
		constructor: OtherCharField(choices=None, other_label=_(u'Other'), hide_relations=None, **kwargs)
		
			* choices		- 	same as CharField
			* other_label	- 	string that will be add to select box as option. When user select this value, text input is automatically displayed. By using this text field user can add another value, which is not in choices.
			


Admin:
------
	
All this modelAdmins is in utilities.admin package
	
	* RelatedToolsAdmin:
	
		adds change and delete button form ForeignKey field
		
	* HiddenModelMixin:
		
		if you do not want to model admin will be seen in index of administration, you can use this mixin. For example::
		
			BookAdmin(HiddenModelMixin, model.Admin):
				pass
				
	* HiddenModelAdmin:
		
		This model admin inherits from HiddenModelMixin and RelatedToolsAdmin::
			HiddenModelAdmin(HiddenModelMixin, RelatedToolsAdmin):
				pass
				
	* MarshallingAdmin:

		If you have two or more models which inherit from the same parent and you want to these models will be displayed at the same admin table, you can use this model admin. 
		Usage:
			firstly you create custom model admin that will inherit from MarshallingAdmin and set parent model and children models. This model admin you use for registration all included models::
				
				CustomMarshallingAdmin(MarshallingAdmin):
					parent = ParentModel
					childs = [ChildModel1, ChildModel2, ...]
				
				admin.site.register(ParentModel, CustomMarshallingAdmin)
				admin.site.register(ChildModel1, CustomMarshallingAdmin)
				admin.site.register(ChildModel2, CustomMarshallingAdmin)
				...
		
		
	* TreeModelMixin:
		
		This admin mixin change list view to tree list view. Objects is displayed in tree structure. You only must set parent varible to model field which point to object parent. For example::
		
			PageModelAdmin(TreeModelMixin, admin.ModelAdmin):
				parent = 'parent_field'


	* CSVExportMixin:
		
		If you want export csv from django administration, you can use this this mixin. You must only inherit this mixin as first parent and set some variables:
		
			* csv_delimiter	-	char which separates values, default is ';'
			* csv_fields	-	fields or object methods which will be exported 
			* csv_quotechar	-	if you can enclose exported values by same char you can use this value. Default is '"'
			* csv_header	-	first row will be formed by field names and short_description of methods, if you set this value to True, default is False
			* csv_bom		-	MS Excel needs special character on the first line, if you set True BOM will be added. Default is False
			* csv_encoding	-	encoding of exported CSV file. Default 'utf-8'
			
			Example::
			
			
				models.py:
				
					Book(models.Model):
						title = models.CharField(u'Title', max_length=255)
						author = models.ForeignKey(Author, verbose_name = u'Author')
   
						get_similar_book(self):
							return algorithm which returns a similar book
						get_similar_book.short_description = u'Similar book'	
							
				admin.py:
					BookCSVExportMixin(CSVExportMixin, admin.ModelAdmin):
						
						    csv_delimiter = ','
	    					csv_fields = ('title', 'author', 'get_similar_book')
						    csv_quotechar = '"'
						    csv_header = True
						    csv_bom = False
						    csv_encoding = ‘iso-8859-1'
			
	
	* CloneModelMixin:
		
		This mixin adds clone button to change form.
		
		
	* MultipleFilesImportMixin:
		
		If you are using inline model admin for files. You can use this mixin for multiple files upload. It uses html 5 and one POST for all files (not working in IE). Mixin calls function received_file for every file in POST. Example::
		
		
			class GalleryAdmin(MultipleFilesImportMixin, admin.ModelAdmin):
		    	inlines = [ImageInLine]
		
		    	def received_file(self, obj, file):
		        	image = Image(image = file, gallery = obj)
		        	image.save()
        
	* AdminPagingMixin:
	
		It adds buttons for next and previous object at change from. This buttons is in object-tools-items block. You can set only one attribute:
			
			* page_ordering - default is 'pk'
			
	
			
			
In the future will be add singnals which automaticly send E-mail when model object is firstly stored and email sender which send HTML emails with images.