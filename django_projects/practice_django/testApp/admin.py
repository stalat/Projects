from django.contrib import admin
from testApp.models import  Student, Movie

class StudentAdmin(admin.ModelAdmin):
	list_display = ['id', 'name', 'marks']

class MovieAdmin(admin.ModelAdmin):
	list_display = ['id', 'moviename', 'actor', 'actress']

admin.site.register(Student, StudentAdmin)
admin.site.register(Movie, MovieAdmin)
