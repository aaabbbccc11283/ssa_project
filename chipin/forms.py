from django import forms
from .models import Group
from .models import Comment
from django import forms
from django.core.exceptions import ValidationError
import mimetypes
from users.models import User

class FileUploadForm(forms.Form):
    file = forms.FileField()
    def clean_file(self):
        file = self.cleaned_data['file']
        # Validate file type (only images allowed)
        mime_type = mimetypes.guess_type(file.name)[0]
        if not mime_type or not mime_type.startswith('image'):
            raise ValidationError("Only image files are allowed.")
        # Validate file size (limit to 2MB)
        if file.size > 2 * 1024 * 1024:
            raise ValidationError("File size exceeds 2MB limit.")
        
        return file

class UserProfilePictureForm(forms.Form):
    picture = forms.ImageField()
    def clean_picture(self):
        picture = self.cleaned_data.get('picture')
        # Restrict file types
        if not picture.content_type.startswith('image'):
            raise forms.ValidationError("Only image files are allowed.")
        
        # Restrict file size (limit to 1MB)
        if picture.size > 1024 * 1024:
            raise forms.ValidationError("The image file is too large (limit: 1MB).")
        
        return picture

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter your comment...'})
        }

    # Clean the content to sanitise input
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if "<script>" in content.lower():  # Prevent XSS by checking for script tags
            raise forms.ValidationError("Invalid content.")
        return content

class GroupCreationForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        group = super().save(commit=False)
        group.admin = self.user  # Assign the logged-in user as the admin
        if commit:
            group.save()
            group.members.add(self.user)  # Add the admin to the members list
        return group

class TopUpForm(forms.ModelForm):
    amount = forms.DecimalField(
        min_value=0.01, decimal_places=2, max_digits=5, label="Amount to Top-Up"
    )
class Meta:
        model = User
        fields = ['amount']