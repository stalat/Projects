# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    description = models.TextField(default='')
    company = models.CharField(max_length=100, blank=False)
    city = models.CharField(max_length=100, default='')
    website = models.URLField(default='')
    phone = models.IntegerField(default=0)
    image = models.ImageField(upload_to='profile_image', blank=True)
    resume = models.FileField(upload_to='resume_folder')

    def __str__(self):
        return self.user.username


class Portfolio(models.Model):    
    image_01 = models.ImageField(upload_to='portfolio_image', blank=True)
    image_02 = models.ImageField(upload_to='portfolio_image', blank=True)
    image_03 = models.ImageField(upload_to='portfolio_image', blank=True)
    image_04 = models.ImageField(upload_to='portfolio_image', blank=True)
    image_05 = models.ImageField(upload_to='portfolio_image', blank=True)
    image_06 = models.ImageField(upload_to='portfolio_image', blank=True)
    image_07 = models.ImageField(upload_to='portfolio_image', blank=True)
    image_08 = models.ImageField(upload_to='portfolio_image', blank=True)


class CompanyProfile(models.Model):
    user = models.ForeignKey(UserProfile)
    company_name = models.CharField(max_length=100)
    company_description = models.TextField(default='')
    designation = models.CharField(max_length=200)
    profile = models.TextField(default='')
    from_date = models.CharField(max_length=100, blank=True)
    to_date = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.company_name