# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
from django.shortcuts import render
from wsgiref.util import FileWrapper
import mimetypes
from django.conf import settings
from django.http import HttpResponse
from sin_app.models import Portfolio, UserProfile, CompanyProfile
from django.views.generic import TemplateView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.shortcuts import render, redirect, reverse

# Authentication mechanism - Approach:1
@login_required
def home(request):
    return render(request, 'registration/success.html', {})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('home')
    form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


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

class DownloadResume(TemplateView):

    def get(request, WSGIRequest):
        file_name = 'talat_parwez.pdf'
        file_path = os.path.join(settings.MEDIA_ROOT, 'resume_folder', file_name)
        file_wrapper = FileWrapper(file(file_path,'rb'))
        file_mimetype = mimetypes.guess_type(file_path)
        response = HttpResponse(file_wrapper, content_type=file_mimetype )
        response['X-Sendfile'] = file_path
        response['Content-Length'] = os.stat(file_path).st_size
        response['Content-Disposition'] = 'attachment; filename=%s/' % str(file_name) 
        return response