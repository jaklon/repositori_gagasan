from django.template.defaulttags import register
from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """ Allows accessing dictionary keys with variables in templates """
    return dictionary.get(key)