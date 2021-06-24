# python level imports
import datetime

# application level imports
from testApp.models import Student
from testApp.forms import StudentRegistrationForm, StudentFeedbackForm
# django level imports
from django.shortcuts import render
from django.http import HttpResponse

# def welcome(request):
# 	s = "<h1>Welcome to Django classes. {0}</h1>".format(str(datetime.datetime.now()))
# 	return HttpResponse(s)

def welcome(request):
	return render(request, 'testApp/mono_wish.html')

def gameRules(request):
	return render(request, 'testApp/game_rules.html')

def playGame(request):
	my_dict = {'keys': [i for i in range(15)]}
	return render(request, 'testApp/pla_card_game.html', context=my_dict)

def tempView(request):
	date = str(datetime.datetime.now())
	my_dict = {'my_date': date, 'name': "Talat Parwez"}
	return render(request, 'testApp/wish.html', context=my_dict)

def staticView(request):
	return render(request, 'testApp/static_content.html')

def studentList(request):
	student_list = Student.objects.all()
	context_dict = {'students': student_list}
	return render(request, 'testApp/student_data.html', context_dict)

def studentRegistration(request):
	form = StudentRegistrationForm()
	return render(request, 'testApp/student_registration.html', {'form': form})

def thankyou_view(request):
	return render(request, 'testApp/thank_you.html')

def studentFeedback(request):
	if request.method == "GET":
		form = StudentFeedbackForm()
	if request.method == "POST":
		form = StudentFeedbackForm(request.POST)
		if form.is_valid():
			print("Form validation success, printing feedback information")
			# print(form.cleaned_data)
			return thankyou_view(request)
	return render(request, 'testApp/student_feedback.html', {'form': form})
	