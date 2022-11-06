from django.urls import re_path as url
from sin_app.views import Home, DownloadResume


app_name = 'sin_app'
urlpatterns = [
    # url('', Home.as_view(), name='home'),     This will target all hits to home views.
    url(r'^$', Home.as_view(), name='home'),
    url(r'resume/$', DownloadResume.as_view(), name='download_resume'),
    # url('home/', Home.as_view(), name='home'),
    # url('gallery/', Gallery.as_view(), name='gallery'),
    # url('mission/',  Mission.as_view(), name='mission'),
              ]
