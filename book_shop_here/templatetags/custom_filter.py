from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter(is_safe=True)
@stringfilter
def replace(value, arg):
    """
    Replaces occurrences of a substring with another in a string.
    Usage: {{ value|replace:"old_substring,new_substring" }}
    """
    if "," not in arg:
        return value  # Handle cases where the argument is not properly formatted

    old_substring, new_substring = arg.split(",", 1)
    return value.replace(old_substring, new_substring)
