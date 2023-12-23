from django import forms
from celeryApp.models import CustomerDetail

class CustomerDetailForm(forms.ModelForm):
    class Meta:
        model = CustomerDetail
        fields = ['name', 'email_account', 'message']