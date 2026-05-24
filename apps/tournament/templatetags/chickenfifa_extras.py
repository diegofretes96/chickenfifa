from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Permite acceder a dict[key] desde templates: {{ dict|get_item:key }}"""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None


@register.filter
def puntos_class(puntos):
    """Devuelve la clase CSS para el badge de puntos."""
    if puntos == 5:
        return "puntos-5"
    if puntos == 3:
        return "puntos-3"
    if puntos == 2:
        return "puntos-2"
    return "puntos-0"
