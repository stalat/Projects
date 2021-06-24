from django import forms

class StudentRegistrationForm(forms.Form):
	name = forms.CharField()
	marks = forms.IntegerField()

class StudentFeedbackForm(forms.Form):
	name = forms.CharField()
	rollno = forms.IntegerField()
	email = forms.EmailField()
	feedback = forms.CharField(widget=forms.Textarea)
	
	def clean_name(self):
		inputname = self.cleaned_data['name']
		if len(inputname) < 4:
			raise forms.ValidationError('Name should atleast be 4 characters')
		return inputname