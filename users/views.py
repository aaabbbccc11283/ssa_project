from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm
from django.contrib.auth.forms import UserCreationForm
import logging

# Set up logger
logger = logging.getLogger(__name__)

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            logger.info(f"User '{user.username}' logged in successfully.")  # Log successful login
            return redirect('home')
        else:
            logger.warning(f"Failed login attempt for username '{username}'.")  # Log failed login
            messages.error(request, "Invalid credentials.")
    return render(request, 'users/login.html')

def logout_view(request):
    logger.info(f"User '{request.user.username}' logged out.")  # Log logout
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect(reverse('login'))

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()  # Automatically hashes the password before saving
            messages.success(request, 'Account created successfully! You can now log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'users/register.html', {'form': form})

def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your account has been created! You can now log in.")
            return redirect('users:login')
    else:
        form = UserRegistrationForm()
    return render(request, 'users/register.html', {'form': form})

@login_required(login_url='users:login')
def user(request):
    return render(request, "users/user.html")

def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', reverse("users:user"))
            return HttpResponseRedirect(next_url)
        else:
            messages.error(request, "Invalid Credentials.")
    return render(request, "users/login.html")

def logout_view(request):
    logout(request)
    messages.success(request, "Successfully logged out.")
    return redirect('users:login')