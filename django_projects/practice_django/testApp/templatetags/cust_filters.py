from django import template
register = template.Library()

def truncate5(value):
	result = value[0:5]
	return result

def truncateN(value, n):
    result = value[0:n]
    return result

register.filter('truncateN', truncateN)

register.filter('truncate5', truncate5)

