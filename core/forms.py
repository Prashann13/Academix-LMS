from django import forms

from .models import AcademicSession, Semester


class AcademicSessionForm(forms.ModelForm):
    class Meta:
        model = AcademicSession
        fields = ["name", "is_current"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "2025/2026"}),
            "is_current": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class SemesterForm(forms.ModelForm):
    class Meta:
        model = Semester
        fields = ["session", "name", "is_current"]
        widgets = {
            "session": forms.Select(attrs={"class": "form-select"}),
            "name": forms.Select(attrs={"class": "form-select"}),
            "is_current": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
