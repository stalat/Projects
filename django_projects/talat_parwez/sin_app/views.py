# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from models import Portfolio, UserProfile, CompanyProfile
from django.views.generic import TemplateView, FormView

# Create your views here.

class Home(TemplateView):
    template_name = 'index.html'

    def get(self, request):
    	images = Portfolio.objects.all()
    	company_details = CompanyProfile.objects.filter(user=1)[::-1]
        user_profile = UserProfile.objects.all()[0]
        response_generated = {
        						'company_details': company_details,
        						'portfolio': images,
        						'user': user_profile
        					}

        return render(request, self.template_name, response_generated)
