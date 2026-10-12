from django.conf import settings
from django.db import models
from django.urls import reverse

from core.models import AcademicSession, Semester
from course.models import Program, Course


class Student(models.Model):
    LEVEL_CHOICES = [
        ("100", "100 Level"),
        ("200", "200 Level"),
        ("300", "300 Level"),
        ("400", "400 Level"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student_profile"
    )
    matric_number = models.CharField(max_length=20, unique=True, blank=True)
    program = models.ForeignKey(
        Program, on_delete=models.SET_NULL, null=True, blank=True, related_name="students"
    )
    level = models.CharField(max_length=3, choices=LEVEL_CHOICES, default="100")
    session_admitted = models.ForeignKey(
        AcademicSession, on_delete=models.SET_NULL, null=True, blank=True
    )
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["user__last_name", "user__first_name"]

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.matric_number:
            self.matric_number = f"STU/{self.pk:05d}"
            super().save(update_fields=["matric_number"])

    def get_absolute_url(self):
        return reverse("student_detail", kwargs={"pk": self.pk})


class TakenCourse(models.Model):
    """A student's academic record for one course in one session/semester."""

    GRADE_CHOICES = [
        ("A", "A"), ("B", "B"), ("C", "C"), ("D", "D"), ("F", "F"), ("", "Not graded"),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="taken_courses")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="taken_by")
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE)
    semester = models.CharField(max_length=10, choices=Semester.Term.choices)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    grade = models.CharField(max_length=2, choices=GRADE_CHOICES, blank=True)

    class Meta:
        unique_together = ("student", "course", "session", "semester")
        ordering = ["-session", "semester", "course"]

    def __str__(self):
        return f"{self.student} - {self.course} ({self.session})"

    def get_absolute_url(self):
        return reverse("record_list")
