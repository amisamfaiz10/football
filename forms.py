from django import forms
from .models import Player,Message

class PlayerFilterForm(forms.Form):
    # Define the filter fields as checkboxes
    country = forms.MultipleChoiceField(
        choices=[(country,country) for country in Player.objects.values_list('country',flat=True).distinct()],
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    age = forms.MultipleChoiceField(
        choices=[(str(age), str(age)) for age in range(16, 41)],
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    position = forms.MultipleChoiceField(
        choices=Player.POSITION_CHOICES,  # Assume Player.POSITION_CHOICES is defined in your Player model
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

