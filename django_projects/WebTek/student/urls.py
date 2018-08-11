from views import home
from django.conf.urls import url, include

urlpatterns = [
    url(r'^$', home, name='home'),
    ]
