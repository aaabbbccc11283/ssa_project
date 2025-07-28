from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError  # ✅ ADDED: for custom validation
from .models import Profile

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    surname = forms.CharField(max_length=30, required=True)
    nickname = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'first_name', 'surname', 'nickname']

    # ✅ ADDED: custom validation to enforce unique nickname
    def clean_nickname(self):
        nickname = self.cleaned_data.get('nickname')
        if Profile.objects.filter(nickname=nickname).exists():
            raise ValidationError("This nickname is already taken.")
        return nickname

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['surname']
        if commit:
            user.save()
            profile = user.profile
            profile.first_name = self.cleaned_data['first_name']
            profile.surname = self.cleaned_data['surname']
            profile.nickname = self.cleaned_data['nickname']
            profile.save()
        return user
