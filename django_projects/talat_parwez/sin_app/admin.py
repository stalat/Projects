# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from sin_app.models import UserProfile, Portfolio, CompanyProfile


# Register your models here.
admin.site.register(UserProfile)
admin.site.register(Portfolio)
admin.site.register(CompanyProfile)
