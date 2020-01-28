from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def local(context, uri):
    return uri.replace(context['settings'].DATA_PREFIX, context['settings'].LOCAL_PREFIX)



@register.simple_tag()
def last_path(uri):
    uri = uri[uri.rfind('/')+1:]
    uri = uri[uri.rfind('#')+1:]
    return uri
