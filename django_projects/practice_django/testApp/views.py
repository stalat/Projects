# python level imports
import datetime

# django level imports
from django.shortcuts import render
from django.http import HttpResponse

def welcome(request):
	s = "<h1>Welcome to Django classes. {0}</h1>".format(str(datetime.datetime.now()))
	return HttpResponse(s)

def tempView(request):
	date = str(datetime.datetime.now())
	my_dict = {'my_date': date, 'name': "Talat Parwez"}
	return render(request, 'testApp/wish.html', context=my_dict)
