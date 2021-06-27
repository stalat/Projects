from django.conf.urls import url
from testApp import views

urlpatterns = [
	url(r'^$',  views.welcome),
	url(r'^tempView',  views.tempView),
	url(r'^staticView',  views.staticView),
	url(r'^studentList',  views.studentList),
	url(r'^registration',  views.studentRegistration),
	url(r'^feedback',  views.studentFeedback),
	url(r'^register',  views.student_view),
	url(r'^movie_index',  views.movie_index),
	url(r'^movie_add',  views.movie_add),
	url(r'^home_news',  views.home_news),
	url(r'^movie_news',  views.movie_news),
	url(r'^sports_news',  views.sports_news),
	url(r'^politics_news',  views.politics_news),
	url(r'^count_view',  views.count_view),
	url(r'^movie_list',  views.movie_list),
	url(r'^game_rules',  views.gameRules),
	url(r'^placard',  views.playGame),
	]