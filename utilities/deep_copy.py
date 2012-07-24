# coding: utf-8
from copy import copy as copy_object

def rename_unique(obj):
    for field in obj._meta.fields:
        if (field.get_internal_type() ==  "CharField" and field.unique):
            origin_val = getattr(obj, field.name)
            val = origin_val
            i = 1
            while (obj.__class__.objects.filter(**{field.name: val})):
                val = origin_val + '(%s)' % i
                i +=1

            setattr(obj, field.name, val)
    

def deep_copy(obj, copy_related = True): 
    
    copied_obj = copy_object(obj) 
    copied_obj.id = None 
    
    if hasattr(copied_obj,'clone'):
        copied_obj.clone() 
    rename_unique(copied_obj)
    copied_obj.save() 
       
    for original, copy in zip(obj._meta.many_to_many, copied_obj._meta.many_to_many): 
        # get the managers of the fields 
        source = getattr(obj, original.attname) 
        destination = getattr(copied_obj, copy.attname) 
        # copy m2m field contents 
        for element in source.all(): 
            destination.add(element) 
          
    # save for a second time (to apply the copied many to many fields) 
    
    if hasattr(copied_obj,'clone'):
        copied_obj.clone() 
    copied_obj.save() 
        
    if (copy_related):   
        # clone related objects
        links = [rel.get_accessor_name() for rel in obj._meta.get_all_related_objects()]
        for link in links:
            for original in getattr(obj, link).all():
                copied_related = deep_copy(original)
                for field in copied_related._meta.fields:
                    #set foreign key to copied_obj
                    if (getattr(copied_related, field.name) == obj):
                        setattr(copied_related, field.name, copied_obj)
                if hasattr(copied_related,'clone'):
                    copied_related.clone() 
                rename_unique(copied_related)
                copied_related.save()
        
    return copied_obj 