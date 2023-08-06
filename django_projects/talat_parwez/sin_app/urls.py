from django.urls import re_path as url
from sin_app.views import Home, DownloadResume, register
from django.contrib.auth import views as auth_views


app_name = 'sin_app'
urlpatterns = [
    url('register/', register, name='register'),
    url('login/', auth_views.LoginView.as_view(), name='login'),
    url('logout/', auth_views.LogoutView.as_view(), name='logout'),
    url(r'^$', Home.as_view(), name='home'),
    url(r'resume/$', DownloadResume.as_view(), name='download_resume'),
    ]
