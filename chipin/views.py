from django.http import HttpResponse 
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.models import User
from .forms import GroupCreationForm
from .models import Group
import urllib.parse
from .models import GroupJoinRequest
from users.models import Profile
from django.db import transaction
from decimal import Decimal
from .models import Event
from users.models import Transaction
from django.shortcuts import render
from django.utils.timezone import now, timedelta
from django.utils import timezone


@login_required
def accept_event(request, event_id):
    event = Event.objects.get(id=event_id)

    if request.method == 'POST':
        event.accepted_by = request.user
        event.save()

        # Apply transaction logic
        amount = event.total_spend
        profile = request.user.profile
        profile.balance += amount
        profile.save()

        Transaction.objects.create(
            user=request.user,
            amount=amount,
            group=event.group.name,
            event=event.name
        )

        messages.success(request, f"You accepted '{event.name}' and received ${amount}!")
        return redirect('users:user')

    return render(request, 'chipin/accept_event.html', {
        'event': event,
    })

@login_required
def home(request):
    user = request.user
    pending_invitations = user.pending_invitations.all() # Get pending group invitations for the current user
    user_groups = user.group_memberships.all()  # Get groups the user is a member of
    user_join_requests = GroupJoinRequest.objects.filter(user=user)  # Get join requests sent by the user
    available_groups = Group.objects.exclude(members=user).exclude(join_requests__user=user) # Get groups the user is not a member of and the user has not requested to join
    context = {
        'pending_invitations': pending_invitations,
        'user_groups': user_groups,
        'user_join_requests': user_join_requests,
        'available_groups': available_groups
    }
    return render(request, 'chipin/home.html', context)

@login_required
def create_group(request):
    if request.method == 'POST':
        form = GroupCreationForm(request.POST, user=request.user)
        if form.is_valid():
            group_name = form.cleaned_data['name']
            if Group.objects.filter(name=group_name).exists():
                messages.error(request, f'A group with the name "{group_name}" already exists. Please choose a different name.')
            else:
                group = form.save()
                messages.success(request, f'Group "{group.name}" created successfully!')
                return redirect('chipin:group_detail', group_id=group.id)
                
    else:
        form = GroupCreationForm(user=request.user)
    return render(request, 'chipin/create_group.html', {'form': form})

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
        user_id = request.POST.get('user_id')
        invited_user = get_object_or_404(User, id=user_id)      
        if invited_user in group.invited_users.all():
            messages.info(request, f'{invited_user.profile.nickname} has already been invited.')
        else:
            group.invited_users.add(invited_user)
            messages.success(request, f'Invitation sent to {invited_user.profile.nickname}.')
        return redirect('chipin:group_detail', group_id=group.id)  
    return render(request, 'chipin/invite_users.html', {
        'group': group,
        'users_not_in_group': users_not_in_group
    })

@login_required
def accept_invite(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    user_id = request.GET.get('user_id')
    if user_id:
        invited_user = get_object_or_404(User, id=user_id)
        if invited_user in group.members.all():
            messages.info(request, f'{invited_user.profile.nickname} is already a member of the group "{group.name}".')
        elif invited_user in group.invited_users.all():
            group.members.add(invited_user)
            group.invited_users.remove(invited_user)  # Remove from invited list
            messages.success(request, f'{invited_user.profile.nickname} has successfully joined the group "{group.name}".')
        else:
            messages.error(request, "You are not invited to join this group.")
    else:
        messages.error(request, "Invalid invitation link.")  
    return redirect('chipin:group_detail', group_id=group.id)

@login_required
def request_to_join_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    # Check if the user is already a member
    if request.user in group.members.all():
        messages.info(request, "You are already a member of this group.")
        return redirect('chipin:home')
    # Check if the user has already submitted a join request
    join_request, created = GroupJoinRequest.objects.get_or_create(user=request.user, group=group)
    if created:
        messages.success(request, "Your request to join the group has been submitted.")
    else:
        messages.info(request, "You have already requested to join this group.")
    return redirect('chipin:home')

@login_required
def delete_join_request(request, request_id):
    join_request = get_object_or_404(GroupJoinRequest, id=request_id, user=request.user)
    # Ensure the logged-in user can only delete their own join requests
    if join_request.user == request.user:
        join_request.delete()
        messages.success(request, "Your join request has been successfully deleted.")
    else:
        messages.error(request, "You are not authorised to delete this join request.")
    return redirect('chipin:home')  
    
@login_required
def leave_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    # Check if the user is a member of the group
    if request.user in group.members.all():
        group.members.remove(request.user)  # Remove the user from the group
        messages.success(request, f'You have left the group {group.name}.')
    else:
        messages.error(request, 'You are not a member of this group.') 
    return redirect('chipin:home')  

@login_required
def vote_on_join_request(request, group_id, request_id, vote):
    group = get_object_or_404(Group, id=group_id)
    join_request = get_object_or_404(GroupJoinRequest, id=request_id) 
    if request.user not in group.members.all():
        messages.error(request, "You must be a member of the group to vote.")
        return redirect('chipin:group_detail', group_id=group.id)  
    if request.user in join_request.votes.all():
        messages.info(request, "You have already voted.")
        return redirect('chipin:group_detail', group_id=group.id)
        
    # Register the user's vote
    join_request.votes.add(request.user)
    
    # Calculate if more than 60% of members have approved
    total_members = group.members.count()
    total_votes = join_request.votes.count() 
    if total_votes / total_members >= 0.6:
        join_request.is_approved = True
        group.members.add(join_request.user)  # Add the user to the group
        join_request.save()
        messages.success(request, f"{join_request.user.profile.nickname} has been approved to join the group!") 
    return redirect('chipin:group_detail', group_id=group.id)

from .models import Group, Comment
from .forms import CommentForm

@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.user != request.user:  # Ensure only the comment author can edit
        return redirect('chipin:group_detail', group_id=comment.group.id)
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('chipin:group_detail', group_id=comment.group.id)
    else:
        form = CommentForm(instance=comment)
    return render(request, 'chipin/edit_comment.html', {'form': form, 'comment': comment})

@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.user == request.user or request.user == comment.group.admin:  # Allow author or group admin to delete
        comment.delete()
    return redirect('chipin:group_detail', group_id=comment.group.id)

from .models import Event

@login_required
def group_detail(request, group_id, edit_comment_id=None):
    group = get_object_or_404(Group, id=group_id)
    is_member = request.user in group.members.all()
    if not is_member:
        messages.error(request, "You cannot view a group you are not in.")
        username = request.POST.get("username")
        return redirect('chipin:home')
    comments = group.comments.all().order_by('-created_at')  # Fetch all comments for the group
    events = group.events.filter(archived=False)   # Fetch all events associated with the group and filter out archived events
    is_member = request.user in group.members.all()
    # Add a new comment or edit an existing comment
    if edit_comment_id: # Fetch the comment to edit, if edit_comment_id is provided
        comment_to_edit = get_object_or_404(Comment, id=edit_comment_id)
        if comment_to_edit.user != request.user:
            return redirect('chipin:group_detail', group_id=group.id)
    else:
        comment_to_edit = None
        
    if request.method == 'POST':
        if not is_member:
            return redirect('chipin:home', group_id=group_id)       
        if comment_to_edit: # Editing an existing comment
            form = CommentForm(request.POST, instance=comment_to_edit)
        else: # Adding a new comment
            form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.group = group
            comment.save()
            return redirect('chipin:group_detail', group_id=group.id)
    else:
        form = CommentForm(instance=comment_to_edit) if comment_to_edit else CommentForm()
    # Calculate event share for each event and check user eligibility
    event_share_info = {}
    for event in events:
        event_share = event.calculate_share()
        user_eligible = request.user.profile.max_spend >= event_share
        user_has_joined = request.user in event.members.all()  # Check if the user has already joined the event
        event_share_info[event] = {
            'share': event_share,
            'eligible': user_eligible,
            'status': event.status,
            'joined': user_has_joined
        }
    # Return data to the template
    return render(request, 'chipin/group_detail.html', {
        'group': group,
        'comments': comments,
        'form': form,
        'comment_to_edit': comment_to_edit,
        'events': events,
        'event_share_info': event_share_info,
    })


@login_required
def create_event(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if request.user != group.admin:
        messages.error(request, "Only the group administrator can create events.")
        return redirect('chipin:group_detail', group_id=group.id)
    if request.method == 'POST':
        event_name = request.POST.get('name')
        event_date = request.POST.get('date')
        total_spend = request.POST.get('total_spend')
        event = Event.objects.create(
            name=event_name,
            date=event_date,
            total_spend=total_spend,
            group=group
        )
        messages.success(request, f'Event "{event_name}" created successfully!')
        return redirect('chipin:group_detail', group_id=group.id)
    return render(request, 'chipin/create_event.html', {'group': group})

@login_required
def join_event(request, group_id, event_id):
    group = get_object_or_404(Group, id=group_id)
    event = get_object_or_404(Event, id=event_id, group=group)

    user = request.user
    profile = user.profile

    if user in event.members.all():
        messages.info(request, "You have already joined this event.")
        return redirect('chipin:group_detail', group_id=group.id)

    # Determine new number of participants including this user
    current_members = event.members.count()
    new_participant_count = current_members + 1
    share = event.total_spend / new_participant_count

    if profile.balance < share:
        messages.error(request, f"You do not have enough balance to join this event. Required: ${share:.2f}")
        return redirect('chipin:group_detail', group_id=group.id)

    # Deduct share and join event
    profile.balance -= share
    profile.save()
    event.members.add(user)
    event.save()

    # Create transaction
    Transaction.objects.create(
        user=user,
        amount=-share,
        group=group.name,
        event=event.name
    )

    messages.success(request, f"You joined '{event.name}' and paid your share of ${share:.2f}.")
    return redirect('chipin:group_detail', group_id=group.id)


@login_required
def update_event_status(request, group_id, event_id):
    group = get_object_or_404(Group, id=group_id)
    event = get_object_or_404(Event, id=event_id, group=group)
    # Ensure that only the group admin can update the event status
    if request.user != group.admin:
        messages.error(request, "Only the group administrator can update the event status.")
        return redirect('chipin:group_detail', group_id=group.id)
    # Calculate the share per member
    event_share = event.calculate_share()
    # Check if all members can afford the event share
    sufficient_funds = True
    for member in group.members.all():
        if member.profile.max_spend < event_share:
            sufficient_funds = False
            break
    # Update the event status based on the members' ability to cover the share
    if sufficient_funds:
        event.status = "Active"
        messages.success(request, f"The event '{event.name}' is now Active. All members can cover the cost.")
    else:
        event.status = "Pending"
        messages.warning(request, f"The event '{event.name}' remains Pending. Some members cannot cover the cost.")
    # Save the updated event status
    event.save()
    return redirect('chipin:group_detail', group_id=group.id)

@login_required
def leave_event(request, group_id, event_id):
    group = get_object_or_404(Group, id=group_id)
    event = get_object_or_404(Event, id=event_id, group=group)
    # Check if the user is part of the event
    if request.user not in event.members.all():
        messages.error(request, "You are not a member of this event.")
        return redirect('chipin:group_detail', group_id=group.id)
    # Remove the user from the event
    event.members.remove(request.user)
    messages.success(request, f"You have successfully left the event '{event.name}'.")
    # Optionally, check if the event status should be updated
    event.check_status()
    event.save()
    return redirect('chipin:group_detail', group_id=group.id)

@login_required
def delete_event(request, group_id, event_id):
    group = get_object_or_404(Group, id=group_id)
    event = get_object_or_404(Event, id=event_id, group=group)
    # Ensure only the group admin can delete the event
    if request.user != group.admin:
        messages.error(request, "Only the group administrator can delete events.")
        return redirect('chipin:group_detail', group_id=group.id)
    # Delete the event
    event.delete()
    messages.success(request, f"The event '{event.name}' has been deleted.")
    return redirect('chipin:group_detail', group_id=group.id)

@login_required 
def transfer_funds(request, group_id, event_id):
    event = get_object_or_404(Event, id=event_id)
    group = get_object_or_404(Group, id=group_id)
    group_members = event.members.all()
    share = event.calculate_share()
    admin_user = event.group.admin
    total_collected = Decimal(0)

    for member in group_members:
        try:
            profile = member.profile
            old_balance = profile.balance
            profile.balance -= Decimal(share)
            profile.save()
            total_collected += Decimal(share)

            print(f"{member.username} in {event.group.name}: balance updated from {old_balance} to {profile.balance}")

            # ✅ Create a transaction for each member
            Transaction.objects.create(
                user=member, amount=-Decimal(share), group=group.name, event=event.name,  # Deducted from user
            )

        except Profile.DoesNotExist:
            pass

    try:
        admin_profile = admin_user.profile
        old_admin_balance = admin_profile.balance
        admin_profile.balance += total_collected
        admin_profile.save()

        print(f"Admin balance updated from {old_admin_balance} to {admin_profile.balance}")

        # ✅ Create a transaction for the admin (total received)
        Transaction.objects.create(
            user=admin_user,
            
            amount=total_collected,  # Admin receives this amount
            group=group.name,
            event=event.name, 
        )

    except Profile.DoesNotExist:
        print(f'No profile found for admin {admin_user.username}')

    event.status = "Archived"
    event.save()

    messages.success(request, "Funds transferred successfully!")
    
    return redirect('chipin:group_detail', group_id=group.id)

@login_required
def archive_event(request, group_id, event_id):
    group = get_object_or_404(Group, id=group_id)
    event = get_object_or_404(Event, id=event_id, group=group)

    if request.user != group.admin:
        messages.error(request, "Only the group administrator can archive events.")
        return redirect('chipin:group_detail', group_id=group.id)

    if event.archived:
        messages.info(request, f"The event '{event.name}' is already archived.")
    else:
        event.archived = True
        event.status = "Archived"  # Optional if you're also using this
        event.save()
        messages.success(request, f"The event '{event.name}' has been archived.")

    return redirect('chipin:group_detail', group_id=group.id)


def archived_events(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    if request.user not in group.members.all():
        messages.error(request, "You cannot view a group you are not in.")
        return redirect('chipin:home')

    archived_events = group.events.filter(archived=True)
    return render(request, 'chipin/archived_events.html', {
        'group': group,
        'archived_events': archived_events
    })

@login_required
def transaction_history(request):
    from users.models import Transaction
    transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')
    events = Event.objects.select_related('group', 'group__admin')  # preload for performance
    return render(request, 'chipin/transaction_history.html', {
        'transactions': transactions,
        'events': events
    })

from django.utils.timezone import now

@login_required
def contact_support(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if request.method == 'POST':
        amount = request.POST.get('amount', 'N/A')
        timestamp = now().strftime('%Y-%m-%d %H:%M:%S')

        users = group.members.all()
        user_list = "\n".join([f"{u.username} ({u.email})" for u in users])

        subject = f"[Support Request] from Group '{group.name}'"
        message = (
            f"A support request has been submitted.\n\n"
            f"Group Name: {group.name}\n"
            f"Group ID: {group.id}\n"
            f"Users in Group:\n{user_list}\n\n"
            f"Requested Amount: ${amount}\n"
            f"Time of Request: {timestamp}\n"
        )

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            ['support@eforge.online'],  # 📬 Change this to your actual support email
            fail_silently=False,
        )

        messages.success(request, "Support request sent successfully.")
        return redirect('chipin:group_detail', group_id=group_id)

@login_required
def contact_support_view(request):
    user = request.user
    recent_cutoff = now().date() - timedelta(days=30)

    groups = user.group_memberships.all()

    # Show all events from user's groups in the last 30 days (including archived)
    recent_events = Event.objects.filter(
        group__in=groups,
        date__gte=recent_cutoff
    ).order_by('-date')

    events = []
    for e in recent_events:
        events.append({
            'id': e.id,
            'name': e.name,
            'amount': e.total_spend,
            'date': e.date,
            'archived': e.archived,
            'group_name': e.group.name
        })

    if request.method == 'POST':
        is_transaction = request.POST.get("is_transaction") == "yes"
        is_old = request.POST.get("is_old") == "yes" if is_transaction else False
        group_name = None
        event_name = None
        txn_date = None

        if is_transaction and not is_old:
            event_id = request.POST.get("event_id")
            try:
                event = Event.objects.get(id=event_id)
                group_name = event.group.name
                event_name = event.name
                txn_date = event.date.strftime('%Y-%m-%d')
            except Event.DoesNotExist:
                pass

        message = request.POST.get("message", "")
        timestamp = now().strftime('%Y-%m-%d %H:%M:%S')

        email_body = (
            f"User: {user.username} ({user.email})\n"
            f"Time of Request: {timestamp}\n"
            f"Related to Transaction: {is_transaction}\n"
        )

        if is_transaction:
            email_body += f"Transaction older than 30 days: {is_old}\n"
            if not is_old:
                email_body += f"Group: {group_name}\nEvent: {event_name}\nTransaction Date: {txn_date}\n"
            else:
                email_body += "User was asked to provide last 4 digits, expiry, and date in message.\n"

        email_body += f"\nUser Message:\n{message}"

        send_mail(
            subject="Support Request from SafeSwap",
            message=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=["harrisonschool666@gmail.com"],
            fail_silently=False
        )

        messages.success(request, "Your support request has been sent.")
        return redirect('chipin:home')

    return render(request, 'chipin/contact_support.html', {
        'groups': groups,
        'events': events
    })
