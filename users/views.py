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
from chipin.models import Event, Group
from .forms import TopUpForm
from django import forms

def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your account has been created! You can now log in.")
            return redirect('users:login')
        else:
            # The form is invalid, return the form to the template
            return render(request, 'users/register.html', {'form': form})
    else:
        form = UserRegistrationForm()
    return render(request, 'users/register.html', {'form': form})

@login_required(login_url='users:login')
def user(request):
    profile = request.user.profile
    transactions = Transaction.objects.filter(user=request.user)  # Fetch user's transactions
    return render(request, 'users/user.html', {
        'user': request.user,
        'balance': profile.balance,
        'transactions': transactions  # Pass transactions to the template
    })


def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Get the next URL, or if not provided, redirect to the user's profile or another page
            next_url = request.GET.get('next')  # Get 'next' parameter if it exists
            if not next_url:  # If no 'next' parameter, redirect to a default page
                next_url = reverse("users:user")  # Redirect to the user profile or any default page
            return redirect(next_url)
        else:
            messages.error(request, "Invalid Credentials.")
    
    return render(request, "users/login.html")

@login_required
def delete_account(request):
    if request.method == 'POST':
        request.user.delete()  # Deletes the user's account and all related data
        messages.success(request, 'Your account has been deleted.')
        return redirect('login')
    return render(request, 'users/delete_account.html')

def logout_view(request):
    logout(request)
    messages.success(request, "Successfully logged out.")
    return redirect('users:login')

@login_required
def top_up(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = TopUpForm(request.POST, instance=profile)
        if form.is_valid():
            amount = form.cleaned_data['top_up_amount']
            profile.balance += amount
            profile.save()
            Transaction.objects.create(
                user=request.user,
                amount=amount,
                group="-",
                event="TopUp"
            )
            messages.success(request, f'Your balance has been increased by ${amount} successfully!')
            return redirect('users:user')
    else:
        form = TopUpForm()

    context = {
        'form': form,
        'user_balance': profile.balance,
        'welcome_message': f"Welcome back, {request.user.first_name}!",
    }
    return render(request, 'users/top_up.html', context)

    
@login_required
def transactions_view(request):
    transactions = Transaction.objects.filter(user=request.user).order_by('created_at').values()  # Oldest first
    balance = request.user.profile.balance  # Assuming the user has a profile with balance

    return render(request, 'users/transactions.html', {
        'transactions': transactions,
        'balance': balance
    })

def user_view(request):
    profile = request.user.profile  # Get the logged-in user's profile
    return render(request, 'users/user.html', {'balance': profile.balance})
