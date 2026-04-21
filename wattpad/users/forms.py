from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import CustomUser
from stories.models import Genre

class CustomUserCreationForm(UserCreationForm):
    selected_genres = forms.ModelMultipleChoiceField(
        queryset=Genre.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select your favorite reading genres."
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = UserCreationForm.Meta.fields + ('selected_genres',)

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            self.save_m2m()
        return user
