from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import AcademicSession, Semester
from course.models import Program, Course, CourseAllocation
from lecturers.models import Lecturer
from students.models import Student, TakenCourse
from news_events.models import NewsAndEvents

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds the database with demo sessions, programs, courses, users, and records."

    @transaction.atomic
    def handle(self, *args, **options):
        session, _ = AcademicSession.objects.get_or_create(
            name="2025/2026", defaults={"is_current": True}
        )
        semester1, _ = Semester.objects.get_or_create(
            session=session, name=Semester.Term.FIRST, defaults={"is_current": True}
        )

        program, _ = Program.objects.get_or_create(
            name="B.Sc. Computer Science",
            defaults={"summary": "A four-year undergraduate computer science program."},
        )

        course1, _ = Course.objects.get_or_create(
            code="CSC101",
            defaults={
                "program": program,
                "title": "Introduction to Programming",
                "credit_units": 3,
                "level": "100",
                "semester": Semester.Term.FIRST,
            },
        )
        course2, _ = Course.objects.get_or_create(
            code="CSC201",
            defaults={
                "program": program,
                "title": "Data Structures and Algorithms",
                "credit_units": 4,
                "level": "200",
                "semester": Semester.Term.FIRST,
            },
        )

        if not User.objects.filter(username="admin").exists():
            admin = User.objects.create_superuser(
                username="admin", email="admin@academix.local", password="AdminPass123!"
            )
            admin.role = User.Role.ADMIN
            admin.first_name = "System"
            admin.last_name = "Administrator"
            admin.save()
            self.stdout.write(self.style.SUCCESS("Created admin / AdminPass123!"))

        lecturer_user, created = User.objects.get_or_create(
            username="lecturer1",
            defaults={
                "email": "lecturer1@academix.local",
                "first_name": "Jane",
                "last_name": "Okafor",
                "role": User.Role.LECTURER,
            },
        )
        if created:
            lecturer_user.set_password("LecturerPass123!")
            lecturer_user.save()
        lecturer_profile, _ = Lecturer.objects.get_or_create(
            user=lecturer_user, defaults={"department": "Computer Science"}
        )

        student_user, created = User.objects.get_or_create(
            username="student1",
            defaults={
                "email": "student1@academix.local",
                "first_name": "Musa",
                "last_name": "Bello",
                "role": User.Role.STUDENT,
            },
        )
        if created:
            student_user.set_password("StudentPass123!")
            student_user.save()
        student_profile, _ = Student.objects.get_or_create(
            user=student_user,
            defaults={"program": program, "level": "100", "session_admitted": session},
        )

        allocation, _ = CourseAllocation.objects.get_or_create(
            lecturer=lecturer_profile, session=session
        )
        allocation.courses.set([course1, course2])

        TakenCourse.objects.get_or_create(
            student=student_profile,
            course=course1,
            session=session,
            semester=Semester.Term.FIRST,
            defaults={"score": 78, "grade": "A"},
        )

        NewsAndEvents.objects.get_or_create(
            title="Welcome to the New Session",
            defaults={
                "summary": "Classes for the 2025/2026 session begin next Monday.",
                "posted_as": NewsAndEvents.PostType.NEWS,
            },
        )

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))
        self.stdout.write("Login credentials:")
        self.stdout.write("  admin      / AdminPass123!")
        self.stdout.write("  lecturer1  / LecturerPass123!")
        self.stdout.write("  student1   / StudentPass123!")
