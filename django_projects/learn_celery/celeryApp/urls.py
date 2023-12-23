from django.urls import path  
from celeryApp.views import post_message
urlpatterns = [  
    path('', post_message, name='create_blog_post')
    ]

