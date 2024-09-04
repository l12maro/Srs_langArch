from django import forms
from .models import TierReference, TranscriptELAN

class TierReferenceForm(forms.ModelForm):
    # Define the ModelChoiceField for sourceTierType
    sourceTierType = forms.ModelChoiceField(
        queryset=TranscriptELAN.objects.values_list('textType', flat=True).distinct(),
        to_field_name='textType',
        empty_label="Select a type",
        required=True
    )

    class Meta:
        model = TierReference
        fields = '__all__'
