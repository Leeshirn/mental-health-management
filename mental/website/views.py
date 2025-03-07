from django.shortcuts import render, redirect 
from django.contrib.auth import authenticate,login, logout 
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages 
from .forms import SignUpForm
from .models import UserProfile
from django.db import models
def home(request):
    return render(request, 'home.html', {})
 
def login_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            try:
                profile = UserProfile.objects.get(user=user)  # Get the UserProfile
                if profile.role == 'professional' and not profile.is_verified:
                    messages.warning(request, 'Your account is pending verification. Please wait for admin approval.')
                    return redirect('login')
                login(request, user)
                messages.success(request, 'You have been logged in.')
                return redirect('home')
            except UserProfile.DoesNotExist:
                # If UserProfile does not exist, create one
                UserProfile.objects.create(user=user, role='patient', is_verified=True)  # Default to patient
                login(request, user)
                messages.success(request, 'You have been logged in.')
                return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
            return redirect('login')
    
    # If the request method is not POST, render the login page
    return render(request, 'login.html', {})
  
def logout_user(request):
  logout(request)
  messages.success(request, 'You have been logged out ')
  return redirect('home')

def register_user(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
          form.save()
          username = form.cleaned_data['username']
          password = form.cleaned_data['password1']
          user = authenticate(username=username, password=password)
          role = form.cleaned_data['role']

          if role == 'patient':
            messages.success(request, 'You have successfully registered. Please log in.')
            return redirect('login')
          else:
            messages.success(request, 'Your account is pending verification. You will be notified once verified.')
            return redirect('home')  # Redirect to a "pending verification" page
    else:
        form = SignUpForm()
    return render(request, 'register.html', {'form': form})

@login_required
def professional_dashboard(request):
    profile = UserProfile.objects.get(user=request.user)

    if profile.role != 'professional':
        messages.error(request, 'Unauthorized access.')
        return redirect('home')

    if not profile.is_verified:
        messages.warning(request, 'Your account is pending verification.')
        return redirect('home')

    return render(request, 'professional_dashboard.html', {})