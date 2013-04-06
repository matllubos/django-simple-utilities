from django import template

register = template.Library()

class QueryNode(template.Node):
    '''
    Helps with updating and changing URL queryes in templates
    '''
    
    def __init__(self, data):
        self.data = data

    def render(self, context):
        params = context['request'].GET.copy()
        for del_params in self.data['remove']:
            if params.has_key(del_params):
                del params[del_params]
        
        for key, value in self.data['new_params'].items():
            params[key] = value.resolve(context)
        return params.urlencode()
    
@register.tag
def get_query_string(parser, token):
    content = token.split_contents()
    args = {
        'new_params': {},
        'remove': []    
        }
    for arg in content[1:]:
        type, values = arg.split(':')
        for value in values.split(','):
            try:
                if type == 'new_params':
                    param = value.split('=')
                    args[type][param[0]] = parser.compile_filter(param[1])
                elif type == 'remove':
                    args[type].append(value)
            except:
                pass

    return QueryNode(args)