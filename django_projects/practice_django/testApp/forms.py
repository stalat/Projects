from django import forms

class StudentRegistrationForm(forms.Form):
	name = forms.CharField()
	marks = forms.IntegerField()

class StudentFeedbackForm(forms.Form):
	name = forms.CharField()
	rollno = forms.IntegerField()
	email = forms.EmailField()
	feedback = forms.CharField(widget=forms.Textarea)
	