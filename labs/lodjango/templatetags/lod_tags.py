from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def local(context, uri):
    return uri.replace(context['settings'].DATA_PREFIX, context['settings'].LOCAL_PREFIX)
