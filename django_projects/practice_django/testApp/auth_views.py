from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.contrib.auth.models import User

from testApp.forms import RegistrationForm

def register_1(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = User.objects.create(username=username, email=email, password=password)
            login(request, user)
            return redirect('profile')
    else:
        form = RegistrationForm()
    context = {'form': form}
    return render(request, 'registration/register_1.html', context)