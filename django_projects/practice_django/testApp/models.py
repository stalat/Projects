from django.db import models

# Create your models here.

class Student(models.Model):
	name = models.CharField(max_length=100)
	marks = models.IntegerField(default=30)

	def __str__(self):
		return self.name

class Movie(models.Model):
	rdate = models.DateField()
	moviename = models.CharField(max_length=30)
	actor = models.CharField(max_length=30)
	actress = models.CharField(max_length=30)
	rating = models.IntegerField()
