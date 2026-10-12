from django import forms

from .models import Program, Course, CourseAllocation


class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ["name", "summary"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "summary": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["program", "title", "code", "credit_units", "level", "semester", "is_elective"]
        widgets = {
            "program": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "credit_units": forms.NumberInput(attrs={"class": "form-control"}),
            "level": forms.Select(attrs={"class": "form-select"}),
            "semester": forms.Select(attrs={"class": "form-select"}),
            "is_elective": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class CourseAllocationForm(forms.ModelForm):
    class Meta:
        model = CourseAllocation
        fields = ["lecturer", "courses", "session"]
        widgets = {
            "lecturer": forms.Select(attrs={"class": "form-select"}),
            "courses": forms.SelectMultiple(attrs={"class": "form-select"}),
            "session": forms.Select(attrs={"class": "form-select"}),
        }
