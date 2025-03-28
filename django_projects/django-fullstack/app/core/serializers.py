# core/serializers.py
from rest_framework import serializers
from .models.person import Person

class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = '__all__'
