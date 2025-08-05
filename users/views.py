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
from .models import Transaction, Profile, UserChangeLog
from chipin.models import Event, Group
from .forms import TopUpForm, UserUpdateForm
from django import forms
from .forms import PasswordChangeCustomForm
from django.contrib.auth import update_session_auth_hash

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
    user = User.objects.get(pk=request.user.id)  # Force fresh fetch
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

@login_required
def user_portal(request):
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user, profile=profile)
        if form.is_valid():
            changes = []

            # Track and apply changes to User model fields
            for field in ['username', 'first_name', 'last_name', 'email']:
                old = getattr(user, field)
                new = form.cleaned_data.get(field)
                if old != new:
                    changes.append((field, old, new))
                    setattr(user, field, new)

            # Track nickname changes from Profile
            old_nickname = profile.nickname
            new_nickname = form.cleaned_data.get('nickname')
            if old_nickname != new_nickname:
                changes.append(('nickname', old_nickname, new_nickname))
                profile.nickname = new_nickname

            # ✅ Save optional fields (not tracked in change log)
            profile.abn = form.cleaned_data.get('abn', '')
            profile.tfn = form.cleaned_data.get('tfn', '')
            profile.billing_address = form.cleaned_data.get('billing_address', '')

            # Save updates
            user.save()
            profile.save()

            # Log changes
            for field, old, new in changes:
                UserChangeLog.objects.create(
                    user=user,
                    field_name=field,
                    old_value=old,
                    new_value=new
                )

            messages.success(request, "Your details were updated successfully.")
            return redirect('users:user_portal')
    else:
        form = UserUpdateForm(instance=user, profile=profile)

    return render(request, 'users/user_portal.html', {
        'form': form,
        'balance': profile.balance
    })



@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeCustomForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password1']
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)

            # ✅ Log the password change
            UserChangeLog.objects.create(
                user=request.user,
                field_name="password",
                old_value=None,
                new_value="Password changed"
            )

            messages.success(request, "Password changed successfully.")
            return redirect('users:user_portal')
    else:
        form = PasswordChangeCustomForm()

    return render(request, 'users/change_password.html', {'form': form})
