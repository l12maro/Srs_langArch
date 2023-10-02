# forms.py
from django import forms

class LanguageForm(forms.Form):
    choices = (
        ('srs', 'Tsuut\'ina'),
        ('eng', 'English'),
    )
    
    radio_field = forms.ChoiceField(
        choices=choices,
        widget=forms.RadioSelect,
    )
