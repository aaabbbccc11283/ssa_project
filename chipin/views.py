from django.http import HttpResponse 
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import GroupCreationForm
from .models import Group
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.models import User
import urllib.parse

@login_required
def group_detail(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    return render(request, 'chipin/group_detail.html', {'group': group})

@login_required
def delete_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if request.user == group.admin:
        group.delete()
        messages.success(request, f'Group "{group.name}" has been deleted.')
    else:
        messages.error(request, "You do not have permission to delete this group.")
    return redirect('chipin:home')

@login_required
def invite_users(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    users_not_in_group = User.objects.exclude(id__in=group.members.values_list('id', flat=True))
    if request.method == 'POST':
        email = request.POST.get('email')
        send_invitation_email(group, email, request)
        messages.success(request, f'Invitation sent to {email}')
        return redirect('chipin:group_detail', group_id=group.id)
    return render(request, 'chipin/invite_users.html', {'group': group, 'users_not_in_group': users_not_in_group})

@login_required
def accept_invite(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    encoded_email = request.GET.get('email')
    if encoded_email:
        invited_email = urllib.parse.unquote(encoded_email)
        invited_user = get_object_or_404(User, email=invited_email)
        if invited_user in group.members.all():
            messages.info(request, f'{invited_user.username} is already a member of the group "{group.name}".')
        else:
            group.members.add(invited_user)
            messages.success(request, f'{invited_user.username} has successfully joined the group "{group.name}".')
    else:
        messages.error(request, "Invalid invitation link.")
    return redirect('chipin:group_detail', group_id=group.id)

def send_invitation_email(group, email, request):
    encoded_email = urllib.parse.quote(email)
    invite_url = request.build_absolute_uri(reverse('chipin:accept_invite', args=[group.id])) + f"?email={encoded_email}"
    subject = f"You have been invited to join the group {group.name}"
    message = (
        f"<p>You have been invited to join the group <strong>{group.name}</strong>.</p>"
        f"<p><a href='{invite_url}'>OK</a></p>"
    )

    send_mail(
        subject,
        '',  # No plain text body, only HTML
        f"ChipIn <mailgun@{settings.ANYMAIL['MAILGUN_SENDER_DOMAIN']}>",
        [email],
        html_message=message,  # The HTML message
    )

def home(request):
    return render(request, "chipin/home.html")

@login_required
def create_group(request):
    if request.method == 'POST':
        form = GroupCreationForm(request.POST, user=request.user)
        if form.is_valid():
            group = form.save()
            messages.success(request, f'Group "{group.name}" created successfully!')
            return redirect('chipin:group_detail', group_id=group.id)
    else:
        form = GroupCreationForm(user=request.user)
    return render(request, 'chipin/create_group.html', {'form': form})