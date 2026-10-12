from django import forms

from .models import Student, TakenCourse


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["program", "level", "session_admitted", "date_of_birth", "address"]
        widgets = {
            "program": forms.Select(attrs={"class": "form-select"}),
            "level": forms.Select(attrs={"class": "form-select"}),
            "session_admitted": forms.Select(attrs={"class": "form-select"}),
            "date_of_birth": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
        }


class TakenCourseForm(forms.ModelForm):
    class Meta:
        model = TakenCourse
        fields = ["student", "course", "session", "semester", "score", "grade"]
        widgets = {
            "student": forms.Select(attrs={"class": "form-select"}),
            "course": forms.Select(attrs={"class": "form-select"}),
            "session": forms.Select(attrs={"class": "form-select"}),
            "semester": forms.Select(attrs={"class": "form-select"}),
            "score": forms.NumberInput(attrs={"class": "form-control"}),
            "grade": forms.Select(attrs={"class": "form-select"}),
        }

    def clean(self):
        cleaned = super().clean()
        score = cleaned.get("score")
        if score is not None:
            if score >= 70:
                cleaned["grade"] = "A"
            elif score >= 60:
                cleaned["grade"] = "B"
            elif score >= 50:
                cleaned["grade"] = "C"
            elif score >= 45:
                cleaned["grade"] = "D"
            else:
                cleaned["grade"] = "F"
        return cleaned


class StudentCSVImportForm(forms.Form):
    """Admin-side upload form for the bulk student import."""

    csv_file = forms.FileField(
        label="CSV file",
        widget=forms.ClearableFileInput(attrs={"class": "form-control", "accept": ".csv"}),
        help_text="Required columns: username, first_name, last_name, email.",
    )
    default_password = forms.CharField(
        label="Password for all imported students",
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        help_text="Leave blank to auto-generate one shared password (shown once after import).",
    )
    skip_duplicates = forms.BooleanField(
        label="Skip rows whose username or email already exists",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        help_text="Unchecked: existing users are updated instead of skipped.",
    )

    def clean_csv_file(self):
        f = self.cleaned_data["csv_file"]
        if not f.name.lower().endswith(".csv"):
            raise forms.ValidationError("Please upload a .csv file.")
        if f.size > 5 * 1024 * 1024:
            raise forms.ValidationError("File too large (max 5 MB).")
        return f

    def clean_default_password(self):
        pw = self.cleaned_data.get("default_password")
        if pw:
            from django.contrib.auth.password_validation import validate_password

            validate_password(pw)
        return pw
