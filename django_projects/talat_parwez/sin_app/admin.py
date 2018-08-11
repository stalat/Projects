# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from models import UserProfile, Portfolio


# Register your models here.
admin.site.register(UserProfile)
admin.site.register(Portfolio)
