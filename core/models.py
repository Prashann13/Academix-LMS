from django.db import models
from django.urls import reverse


class AcademicSession(models.Model):
    """e.g. '2024/2025'."""

    name = models.CharField(max_length=20, unique=True, help_text="e.g. 2024/2025")
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_current:
            AcademicSession.objects.exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("session_list")


class Semester(models.Model):
    class Term(models.TextChoices):
        FIRST = "FIRST", "First Semester"
        SECOND = "SECOND", "Second Semester"

    session = models.ForeignKey(
        AcademicSession, on_delete=models.CASCADE, related_name="semesters"
    )
    name = models.CharField(max_length=10, choices=Term.choices)
    is_current = models.BooleanField(default=False)

    class Meta:
        unique_together = ("session", "name")
        ordering = ["session", "name"]

    def __str__(self):
        return f"{self.get_name_display()} - {self.session}"

    def save(self, *args, **kwargs):
        if self.is_current:
            Semester.objects.exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("semester_list")
