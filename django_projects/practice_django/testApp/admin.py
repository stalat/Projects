from django.contrib import admin
from testApp.models import  Student

class StudentAdmin(admin.ModelAdmin):
	list_display = ['id', 'name', 'marks']

admin.site.register(Student, StudentAdmin)
