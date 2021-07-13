from django.shortcuts import render, redirect
from django.http import HttpResponse,  HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.views.generic import View, TemplateView

class HelloWorldView(View):
	def get(self, request):
		return HttpResponse('<h1>This is from class Based views</h1>')