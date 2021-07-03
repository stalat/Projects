from django import forms
from django.core import validators
from testApp.models import Student, Movie


def starts_with_t(value):
    if value[0] != 't':
        raise forms.ValidationError('Name should start with t')

class StudentRegistrationForm(forms.Form):
	name = forms.CharField()
	marks = forms.IntegerField()

class StudentFeedbackForm(forms.Form):
	# name = forms.CharField(validators=[starts_with_t])
	name = forms.CharField()
	rollno = forms.IntegerField()
	email = forms.EmailField(label='Email Account')
	password  = forms.CharField(label='Password', widget=forms.PasswordInput)
	rpassword = forms.CharField(label='Password (again)', widget=forms.PasswordInput)
	feedback = forms.CharField(widget=forms.Textarea, validators=[validators.MaxLengthValidator(40), 
		validators.MinLengthValidator(10)])
	bot_handler = forms.CharField(required=False, widget=forms.HiddenInput)
	
	# def clean_name(self):
	# 	inputname = self.cleaned_data['name']
	# 	if len(inputname) < 4:
	# 		raise forms.ValidationError('Name should atleast be 4 characters')
	# 	return inputname

	def clean(self):
		cleaned_data = super(StudentFeedbackForm, self).clean()
		inputbot = cleaned_data['bot_handler']
		if len(inputbot) > 0:
			raise forms.ValidationError('Bot send this request')
		inputname = cleaned_data['name']
		if len(inputname) < 4:
			raise forms.ValidationError('Name should atleast be 4 characters')

		inputfeedback = cleaned_data['feedback']
		if 'feedback' not in inputfeedback:
			raise forms.ValidationError('Feedback keyword is expected')

		inputpwd = cleaned_data['password']
		inputrpwd = cleaned_data['rpassword']
		if inputpwd != inputrpwd:
			raise forms.ValidationError('Passwords does not match!')

		return cleaned_data

class StudentForm(forms.ModelForm):
	class Meta:
		model = Student
		fields = '__all__'

class MovieForm(forms.ModelForm):
	class Meta:
		model = Movie
		fields = '__all__'

class NameForm(forms.Form):
	name = forms.CharField()

class AgeForm(forms.Form):
	age = forms.IntegerField()

class QualificationForm(forms.Form):
	qualification = forms.CharField()

class AddItemForm(forms.Form):
	name = forms.CharField()
	quantity = forms.IntegerField()