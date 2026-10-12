from django import template

register = template.Library()


@register.filter
def getattribute(obj, attr_name):
    """
    Template filter allowing dynamic attribute lookup:
        {{ obj|getattribute:"some_field" }}
    Falls back gracefully if the attribute doesn't exist or is a
    ForeignKey/callable.
    """
    if obj is None:
        return ""
    try:
        value = getattr(obj, attr_name)
    except AttributeError:
        return ""
    if callable(value):
        try:
            value = value()
        except TypeError:
            return ""
    return value


@register.filter
def field_label(value):
    """
    Turns internal field/accessor names into friendly column headers:
    'get_level_display' -> 'Level', 'session_admitted' -> 'Session Admitted'
    """
    s = value
    if s.startswith("get_") and s.endswith("_display"):
        s = s[4:-8]
    return s.replace("_", " ").title()
