from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, TopUpForm
import requests
from django.conf import settings
from django.contrib.auth.models import User
from .models import Transaction

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
    profile = request.user.profile
    return render(request, 'users/user.html', {
        'user': request.user,
        'balance': profile.balance
    })

def logout_view(request):
    logout(request)
    messages.success(request, "Successfully logged out.")
    return redirect('users:login')

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Redirect to the next URL if provided, else default to user profile
            next_url = request.GET.get('next', reverse("users:user"))  # Simplified fallback
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, "users/login.html")

@login_required
def delete_account(request):
    if request.method == 'POST':
        request.user.delete()  # Deletes the user's account and all related data
        messages.success(request, 'Your account has been deleted.')
        return redirect('login')
    return render(request, 'users/delete_account.html')

def user_view(request):
    profile = request.user.profile  # Get the logged-in user's profile
    return render(request, 'users/user.html', {'balance': profile.balance})

@login_required
def top_up(request):
    profile = request.user.profile  # Get the logged-in user's profile
    if request.method == 'POST':
        form = TopUpForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['top_up_amount']
            profile.balance += amount
            profile.save()
            Transaction.objects.create(user=request.user, amount=amount)
            messages.success(request, f'Your balance had been increased by $"{amount}" successfully!')
            return redirect('users:user')
        else:
            return render(request, 'users/top_up.html', {'form': form})
    else:
        form = TopUpForm()
        context = {'form': form, 'user_balance': request.user.profile.balance,'welcome_message': f"Welcome back, {request.user.username}!",}
        return render(request, 'users/top_up.html', context)