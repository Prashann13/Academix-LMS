from django.conf import settings
from django.db import models
from django.urls import reverse

from core.models import AcademicSession, Semester


class Program(models.Model):
    """Degree program / department, e.g. 'B.Sc. Computer Science'."""

    name = models.CharField(max_length=150, unique=True)
    summary = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("program_list")


class Course(models.Model):
    LEVEL_CHOICES = [
        ("100", "100 Level"),
        ("200", "200 Level"),
        ("300", "300 Level"),
        ("400", "400 Level"),
    ]

    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="courses")
    title = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    credit_units = models.PositiveSmallIntegerField(default=3)
    level = models.CharField(max_length=3, choices=LEVEL_CHOICES, default="100")
    semester = models.CharField(
        max_length=10, choices=Semester.Term.choices, default=Semester.Term.FIRST
    )
    is_elective = models.BooleanField(default=False)

    class Meta:
        ordering = ["level", "code"]

    def __str__(self):
        return f"{self.code} - {self.title}"

    def get_absolute_url(self):
        return reverse("course_list")


class CourseAllocation(models.Model):
    """Assigns a lecturer to teach a set of courses for a session."""

    lecturer = models.ForeignKey(
        "lecturers.Lecturer", on_delete=models.CASCADE, related_name="allocations"
    )
    courses = models.ManyToManyField(Course, related_name="allocations")
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("lecturer", "session")

    def __str__(self):
        return f"{self.lecturer} - {self.session}"

    def get_absolute_url(self):
        return reverse("allocation_list")
