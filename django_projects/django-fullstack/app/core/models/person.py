# core/models/person.py
from django.db import models
from .base import TimeStampedModel

class Person(TimeStampedModel):
    name = models.CharField(max_length=100)
    age = models.IntegerField()

    def __str__(self):
        return self.name

class YoungPersonManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(age__lt=25)

class YoungPerson(Person):
    objects = YoungPersonManager()

    class Meta:
        proxy = True
