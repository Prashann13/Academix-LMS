from django import forms

from .models import NewsAndEvents


class NewsAndEventsForm(forms.ModelForm):
    class Meta:
        model = NewsAndEvents
        fields = ["title", "summary", "posted_as", "event_date"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "summary": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "posted_as": forms.Select(attrs={"class": "form-select"}),
            "event_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }
