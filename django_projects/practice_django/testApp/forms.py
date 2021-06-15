from django import forms

class StudentRegistrationForm(forms.Form):
	name = forms.CharField()
	marks = forms.IntegerField()