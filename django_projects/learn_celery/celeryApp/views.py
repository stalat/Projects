import time
from celeryApp.models import CustomerDetail
from celeryApp.forms import CustomerDetailForm
from django.shortcuts import render, redirect


def post_message(request):
    if request.method == 'POST':
        form = CustomerDetailForm(request.POST)
        if form.is_valid():
            time.sleep(5)
            print("Sending an email, Time intensive task")
            return render(request, 'celeryApp/success.html')
    else:
        form = CustomerDetailForm()

    return render(request, 'celeryApp/feedback_form.html', {'form': form})