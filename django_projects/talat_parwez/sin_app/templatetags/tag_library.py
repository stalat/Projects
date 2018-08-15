from django import template

register = template.Library()

@register.filter()
def to_int(value):
    if value % 2 == 0:
    	return "timeline-inverted"