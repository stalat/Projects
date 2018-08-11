# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save

# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    description = models.CharField(max_length=100, default='')
    city = models.CharField(max_length=100, default='')
    website = models.URLField(default='')
    phone = models.IntegerField(default=0)
    image = models.ImageField(upload_to='profile_image', blank=True)

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

    # def create_profile(sender, **kwargs):
    #     if kwargs['created']:
    #         user_profile = UserProfile.objects.create(user=kwargs['instance'])

    # post_save.connect(create_profile, sender=User)
