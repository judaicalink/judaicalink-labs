from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def local(context, uri):
    data_prefix = context['settings'].DATA_PREFIX
    local_prefix = context['settings'].LOCAL_PREFIX
    if 'VIEW_PATH' in context:
        local_prefix += context['VIEW_PATH']
    return uri.replace(data_prefix, local_prefix)



@register.simple_tag()
def last_path(uri):
    uri = uri[uri.rfind('/')+1:]
    uri = uri[uri.rfind('#')+1:]
    return uri
