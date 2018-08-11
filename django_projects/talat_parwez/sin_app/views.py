# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from models import Portfolio, UserProfile
from django.views.generic import TemplateView, FormView

# Create your views here.

class Home(TemplateView):
    template_name = 'index.html'

    def get(self, request):
    	images = Portfolio.objects.all()
        user_profile = UserProfile.objects.all()[0]
        return render(request, self.template_name, {'portfolio': images, 'user': user_profile})
