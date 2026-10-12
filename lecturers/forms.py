from django import forms

from .models import Lecturer


class LecturerForm(forms.ModelForm):
    class Meta:
        model = Lecturer
        fields = ["department", "office"]
        widgets = {
            "department": forms.TextInput(attrs={"class": "form-control"}),
            "office": forms.TextInput(attrs={"class": "form-control"}),
        }
