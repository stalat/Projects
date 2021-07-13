from django.shortcuts import render, redirect
from django.http import HttpResponse,  HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.views.generic import View, TemplateView, ListView, DetailView

from testApp.models import Student, Movie


class HelloWorldView(View):
	def get(self, request):
		return HttpResponse('<h1>This is from class Based views</h1>')

class HelloWorldTemplateView(TemplateView):
	template_name = "testApp/cbf_templates/results.html"


class HelloWorldTemplateContext(TemplateView):
	template_name = "testApp/cbf_templates/info.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['name'] = "Rahul"
		context['subject'] = "Python"
		return context

class MovieListView(ListView):
	model = Movie
	# default template will be movie_list.html
	# default context object will be movie_list

class MovieDetailView(DetailView):
	model = Movie
	# default template will be movie_detail.html
	# default context object will be movie or object