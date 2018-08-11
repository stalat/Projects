"""
WSGI config for talat_parwez project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

import os
import sys
import site
# Add the site-packages of the chosen virtualenv to work with
#site.addsitedir('/var/www/.virtualenvs/exampleenv/local/lib/python2.7/site-packages')
# Add the app's directory to the PYTHONPATH
sys.path.append('/var/www/django_site/talat_parwez')
os.environ['DJANGO_SETTINGS_MODULE'] = 'talat_parwez.settings'
# Activate your virtual env
#activate_env=os.path.expanduser("/var/www/.virtualenvs/exampleenv/bin/activate_this.py")
#execfile(activate_env, dict(__file__=activate_env))
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
