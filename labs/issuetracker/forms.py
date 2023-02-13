from django import forms
from .models import Issue

class IssueForm(forms.Form):
    description = forms.CharField(max_length=1000, required=True)
    triple = forms.CharField(max_length=1000, required=True)

    class Meta:
        model = Issue
        fields = ['description', 'triple']

        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'triple': forms.TextInput(attrs={'class': 'form-control'}),
        }

        labels = {
            'description': 'Description',
            'triple': 'Triple',
        }

        help_texts = {
            'description': 'Please describe the issue',
            'triple': 'Please enter the triple',
        }

        error_messages = {
            'description': {
                'max_length': "This description is too long.",
                'min_length': 'This description is too short.',
                'required': 'Please enter a description',
            },
            'triple': {
                'max_length': "This triple is too long.",
                'required': 'Please enter a triple',
            },
        }