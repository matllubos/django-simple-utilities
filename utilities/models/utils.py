from django.db.models import Q


def filter_to_ors(filter_dict):
    output = None
    for name, value in filter_dict.items():
        if not output:
            output = Q(**{name:value})
        else:
            output |= Q(**{name:value})
    return output