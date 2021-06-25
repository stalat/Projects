from django import forms
from django.core import validators

class StudentRegistrationForm(forms.Form):
	name = forms.CharField()
	marks = forms.IntegerField()

def starts_with_t(value):
    if value[0] != 't':
        raise forms.ValidationError('Name should start with t')

class StudentFeedbackForm(forms.Form):
	# name = forms.CharField(validators=[starts_with_t])
	name = forms.CharField()
	rollno = forms.IntegerField()
	email = forms.EmailField()
	feedback = forms.CharField(widget=forms.Textarea, validators=[validators.MaxLengthValidator(40), 
		validators.MinLengthValidator(10)])
	
	# def clean_name(self):
	# 	inputname = self.cleaned_data['name']
	# 	if len(inputname) < 4:
	# 		raise forms.ValidationError('Name should atleast be 4 characters')
	# 	return inputname

	def clean(self):
		print("Validating whole form")
		cleaned_data = super(StudentFeedbackForm, self).clean()
		print(cleaned_data)
		inputname = cleaned_data['name']
		if len(inputname) < 4:
			raise forms.ValidationError('Name should atleast be 4 characters')

		inputfeedback = cleaned_data['feedback']
		if 'feedback' not in inputfeedback:
			raise forms.ValidationError('Feedback keyword is expected')

		return cleaned_data