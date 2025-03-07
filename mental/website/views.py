from django.shortcuts import render, redirect, get_object_or_404 
from django.contrib.auth import authenticate,login, logout 
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages 
from .forms import SignUpForm
from .models import UserProfile
from django.db import models
def home(request):
    return render(request, 'home.html', {})

def login_user(request):
  
  #Check to see if logging in 
  if request.method == "POST":
    username = request.POST.get('username')
    password = request.POST.get('password')
    #Authenticate
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request,user)
        messages.success(request, 'You have been logged in')
        return redirect('home')
    else: 
      messages.success(request,"There was an error logging in, please try again")
      return redirect('login')
  else:
   return render(request,'login.html',{})
 
def logout_user(request):
  logout(request)
  messages.success(request, 'You have been logged out ')
  return redirect('home')

def register_user(request):
  
  if request.method == 'POST':
    form = SignUpForm(request.POST)
    if form.is_valid():
      form.save()
      #user authentication
      username = form.cleaned_data['username']
      password = form.cleaned_data['password1']
      user = authenticate(username=username,password=password)
      login(request,user)
      messages.success(request,'You have successfully registered, welcome')
      return redirect('login')
  else:
    form=SignUpForm() 
    return render(request, 'register.html', {'form':form})
  return render(request, 'register.html', {'form':form})