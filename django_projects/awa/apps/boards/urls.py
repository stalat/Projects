from views import home
from views import board_topics
from django.conf.urls import url, include

urlpatterns = [
    url(r'^$', home, name='home'),
    #url(r'^about/$', views.about, name='about'), # Just an example
    url(r'(?P<pk>\d+)/$', board_topics, name='board_topics'),
    ]
