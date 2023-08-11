from django import forms

from .models import Tweet


class TweetCreateForm(forms.ModelForm):
    class Meta:
        model = Tweet
        fields = [
            "content",
        ]
