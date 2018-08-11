# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.views.generic import TemplateView, FormView

# Create your views here.

class Home(TemplateView):
    template_name = 'index.html'

    def get(self, request):
        return render(request, self.template_name)
