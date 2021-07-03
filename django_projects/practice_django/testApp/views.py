# python level imports
import datetime

# application level imports
from testApp.models import Student, Movie
from testApp.forms import StudentRegistrationForm, StudentFeedbackForm, StudentForm,  MovieForm
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
	
def student_view(request):
	form = StudentForm()
	if request.method == "POST":
		form = StudentForm(request.POST)
		if form.is_valid():
			form.save(commit=True)
	return render(request, 'testApp/register.html', {'form': form})

def movie_index(request):
	movies_count = Movie.objects.count()
	return render(request, 'testApp/movie_index.html', {'movie_count': movies_count})

def movie_add(request):
	form = MovieForm()
	if request.method == "POST":
		form = MovieForm(request.POST)
		if form.is_valid():
			form.save(commit=True)
		return movie_index(request)
	return render(request, 'testApp/movie_add.html', {'form': form})

def movie_list(request):
	movies_list = Movie.objects.all()
	context_dict = {'movies': movies_list}
	return render(request, 'testApp/movies_list.html', context_dict)

def home_news(request):
	return render(request, 'testApp/news_portal/home_news.html')
	
def movie_news(request):
	return render(request, 'testApp/news_portal/movie_news.html')

def sports_news(request):
	return render(request, 'testApp/news_portal/sport_news.html')

def politics_news(request):
	return render(request, 'testApp/news_portal/politics_news.html')

def count_view(request):
	count = int(request.COOKIES.get('count', 0))
	updated_count = count + 1
	response = render(request, 'testApp/session_manage/count_view.html', context={'count': updated_count})
	response.set_cookie('count', updated_count, max_age=100)
	return response

def page_count_view(request):
    count = request.session.get('count', 0)
    updated_count = count + 1
    print(request.session.get_expiry_age())
    print(request.session.get_expiry_date())
    response = render(request, 'testApp/session_manage/count_view.html', context={'count': updated_count})
    request.session['count'] = updated_count
    return response

def save_name(request):
	return render(request, 'testApp/session_manage/save_name.html')

def save_age(request):
	name = request.GET['name']
	response = render(request, 'testApp/session_manage/save_age.html')
	response.set_cookie('name', name)
	return response

def save_qualification(request):
	age = request.GET['age']
	response = render(request, 'testApp/session_manage/save_qualification.html')
	response.set_cookie('age', age)
	return response

def display_results(request):
	name = request.COOKIES.get('name')
	age = request.COOKIES.get('age')
	qualification = request.GET['qualification']
	context_dict = {'name': name, 'age': age, 'qualification': qualification}
	return render(request, 'testApp/session_manage/display_results.html', context=context_dict)