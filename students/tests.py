"""
Tests for the bulk student CSV import.

Two layers are covered:

* ``students.services.import_students_csv`` — the import engine shared by
  the admin web view and the ``import_students`` management command.
* ``StudentCSVImportView`` — the admin-only upload page.

The final test case runs the committed edge-case fixture at
``students/tests_data/test_students.csv``, which deliberately contains
every failure mode the importer is expected to handle.
"""

import io
import tempfile
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from core.models import AcademicSession
from course.models import Program
from students.models import Student
from students.services import import_students_csv

PROGRAM_NAME = "B.Sc. Computer Science"
FIXTURE = Path(__file__).resolve().parent / "tests_data" / "test_students.csv"

CSV_HEADER = (
    "username,first_name,last_name,email,phone_number,"
    "program,level,date_of_birth,address\n"
)


def make_csv(rows, header=CSV_HEADER):
    """Build an in-memory CSV upload from a list of data-row strings."""
    return io.BytesIO((header + "".join(rows)).encode("utf-8"))


class ImportTestCase(TestCase):
    """Shared fixtures: a matching program and a current academic session."""

    def setUp(self):
        self.program = Program.objects.create(name=PROGRAM_NAME)
        self.session = AcademicSession.objects.create(
            name="2024/2025", is_current=True
        )


class ImportStudentsCsvTests(ImportTestCase):
    def test_creates_users_and_student_profiles(self):
        result = import_students_csv(
            make_csv([
                f"s1,Ada,Lovelace,ada@example.com,,{PROGRAM_NAME},100,2006-01-01,Lagos\n",
                f"s2,Alan,Turing,alan@example.com,,{PROGRAM_NAME},200,2005-02-02,Abuja\n",
            ]),
            default_password="TestPass123!",
        )

        self.assertEqual(
            result["summary"],
            {"total": 2, "created": 2, "skipped": 0, "updated": 0, "failed": 0},
        )

        user = User.objects.get(username="s1")
        self.assertEqual(user.role, User.Role.STUDENT)
        self.assertEqual(user.first_name, "Ada")
        self.assertTrue(user.check_password("TestPass123!"))

        profile = user.student_profile
        self.assertEqual(profile.program, self.program)
        self.assertEqual(profile.level, "100")
        self.assertEqual(profile.session_admitted, self.session)
        self.assertEqual(str(profile.date_of_birth), "2006-01-01")
        self.assertEqual(profile.address, "Lagos")

    def test_matric_numbers_are_sequential(self):
        import_students_csv(
            make_csv([
                "s1,Ada,Lovelace,ada@example.com,,,100,,\n",
                "s2,Alan,Turing,alan@example.com,,,100,,\n",
                "s3,Grace,Hopper,grace@example.com,,,100,,\n",
            ]),
            default_password="TestPass123!",
        )

        matric = list(
            Student.objects.order_by("id").values_list("matric_number", flat=True)
        )
        self.assertEqual(matric, ["STU/00001", "STU/00002", "STU/00003"])

    def test_all_imported_users_share_one_password_hash(self):
        """The importer hashes the password once and reuses it for every row."""
        import_students_csv(
            make_csv([
                "s1,Ada,Lovelace,ada@example.com,,,100,,\n",
                "s2,Alan,Turing,alan@example.com,,,100,,\n",
                "s3,Grace,Hopper,grace@example.com,,,100,,\n",
            ]),
            default_password="TestPass123!",
        )

        hashes = set(User.objects.values_list("password", flat=True))
        self.assertEqual(len(hashes), 1)
        self.assertTrue(all(u.check_password("TestPass123!") for u in User.objects.all()))

    def test_generated_password_when_none_supplied(self):
        result = import_students_csv(make_csv(["s1,Ada,Lovelace,ada@example.com,,,100,,\n"]))

        generated = result["generated_password"]
        self.assertIsNotNone(generated)
        self.assertGreaterEqual(len(generated), 8)
        self.assertTrue(User.objects.get(username="s1").check_password(generated))

    def test_no_generated_password_when_one_is_supplied(self):
        result = import_students_csv(
            make_csv(["s1,Ada,Lovelace,ada@example.com,,,100,,\n"]),
            default_password="TestPass123!",
        )
        self.assertIsNone(result["generated_password"])

    def test_accepts_a_utf8_bom(self):
        """Excel writes a BOM; the header must still parse."""
        content = "﻿" + CSV_HEADER + "s1,Ada,Lovelace,ada@example.com,,,100,,\n"
        result = import_students_csv(
            io.BytesIO(content.encode("utf-8")), default_password="TestPass123!"
        )
        self.assertEqual(result["summary"]["created"], 1)

    def test_accepts_a_filesystem_path(self):
        with tempfile.NamedTemporaryFile(
            "w", suffix=".csv", delete=False, encoding="utf-8", newline=""
        ) as handle:
            handle.write(CSV_HEADER + "s1,Ada,Lovelace,ada@example.com,,,100,,\n")
            path = handle.name

        result = import_students_csv(path, default_password="TestPass123!")
        self.assertEqual(result["summary"]["created"], 1)


class CsvRowValidationTests(ImportTestCase):
    def test_duplicate_username_inside_file_fails_that_row(self):
        result = import_students_csv(
            make_csv([
                "s1,Ada,Lovelace,ada@example.com,,,100,,\n",
                "s1,Alan,Turing,alan@example.com,,,100,,\n",
            ]),
            default_password="TestPass123!",
        )
        self.assertEqual(result["summary"]["created"], 1)
        self.assertEqual(result["summary"]["failed"], 1)
        failed = [r for r in result["rows"] if r.action == "failed"][0]
        self.assertEqual(failed.line, 3)
        self.assertIn("duplicate username", failed.messages[0])

    def test_duplicate_email_inside_file_fails_that_row(self):
        """
        Regression test: a row reusing an email claimed earlier in the same
        file must fail cleanly rather than raising IntegrityError inside
        bulk_create.
        """
        result = import_students_csv(
            make_csv([
                "s1,Ada,Lovelace,shared@example.com,,,100,,\n",
                "s2,Alan,Turing,shared@example.com,,,100,,\n",
            ]),
            default_password="TestPass123!",
        )
        self.assertEqual(result["summary"]["created"], 1)
        self.assertEqual(result["summary"]["failed"], 1)
        failed = [r for r in result["rows"] if r.action == "failed"][0]
        self.assertEqual(failed.line, 3)
        self.assertIn("duplicate email", failed.messages[0])
        self.assertEqual(User.objects.count(), 1)

    def test_missing_required_fields_fail_the_row(self):
        result = import_students_csv(
            make_csv([
                ",Ada,Lovelace,ada@example.com,,,100,,\n",
                "s2,,Turing,alan@example.com,,,100,,\n",
                "s3,Grace,Hopper,not-an-email,,,100,,\n",
            ]),
            default_password="TestPass123!",
        )
        self.assertEqual(result["summary"]["failed"], 3)
        self.assertEqual(result["summary"]["created"], 0)

    def test_bad_values_warn_but_still_import(self):
        result = import_students_csv(
            make_csv(["s1,Ada,Lovelace,ada@example.com,,No Such Program,250,31-02-2006,\n"]),
            default_password="TestPass123!",
        )

        self.assertEqual(result["summary"]["created"], 1)
        self.assertEqual(len(result["rows"][0].messages), 3)

        profile = Student.objects.get(user__username="s1")
        self.assertEqual(profile.level, "100")
        self.assertIsNone(profile.date_of_birth)
        self.assertIsNone(profile.program)

    def test_missing_required_column_raises_before_any_write(self):
        with self.assertRaises(ValueError) as ctx:
            import_students_csv(
                io.BytesIO(b"first_name,last_name\nAda,Lovelace\n"),
                default_password="TestPass123!",
            )
        self.assertIn("username", str(ctx.exception))
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(Student.objects.count(), 0)


class DuplicateHandlingTests(ImportTestCase):
    def setUp(self):
        super().setUp()
        self.existing = User.objects.create_user(
            username="s1",
            email="ada@example.com",
            password="TestPass123!",
            first_name="Old",
            last_name="Name",
            role=User.Role.STUDENT,
        )

    def test_skip_duplicates_is_the_default(self):
        result = import_students_csv(
            make_csv([f"s1,Ada,Lovelace,ada@example.com,,{PROGRAM_NAME},200,,\n"]),
            default_password="TestPass123!",
        )
        self.assertEqual(result["summary"]["skipped"], 1)
        self.assertEqual(result["summary"]["created"], 0)
        self.existing.refresh_from_db()
        self.assertEqual(self.existing.first_name, "Old")

    def test_update_mode_refreshes_the_existing_user(self):
        result = import_students_csv(
            make_csv([f"s1,Ada,Lovelace,ada@example.com,,{PROGRAM_NAME},200,,\n"]),
            default_password="TestPass123!",
            skip_duplicates=False,
        )
        self.assertEqual(result["summary"]["updated"], 1)

        self.existing.refresh_from_db()
        self.assertEqual(self.existing.first_name, "Ada")
        self.assertEqual(self.existing.student_profile.level, "200")

    def test_email_owned_by_another_user_is_skipped(self):
        User.objects.create_user(
            username="other", email="taken@example.com", password="TestPass123!"
        )
        result = import_students_csv(
            make_csv(["s9,Alan,Turing,taken@example.com,,,100,,\n"]),
            default_password="TestPass123!",
        )
        self.assertEqual(result["summary"]["skipped"], 1)
        self.assertFalse(User.objects.filter(username="s9").exists())

    def test_rerunning_the_same_file_is_idempotent(self):
        rows = [f"s1,Ada,Lovelace,ada@example.com,,{PROGRAM_NAME},200,,\n"]
        import_students_csv(make_csv(rows), default_password="TestPass123!")
        result = import_students_csv(make_csv(rows), default_password="TestPass123!")

        self.assertEqual(result["summary"]["created"], 0)
        self.assertEqual(result["summary"]["skipped"], 1)
        self.assertEqual(User.objects.filter(username="s1").count(), 1)


class RealFixtureTests(ImportTestCase):
    """
    Runs the committed edge-case CSV end to end.

    The file holds 21 data rows: 17 valid and 4 deliberately broken
    (blank username, an email reused from an earlier row, a username
    reused from an earlier row, and a malformed address). Three further
    rows carry recoverable problems that must produce warnings rather
    than failures.
    """

    def _run(self):
        with FIXTURE.open("rb") as handle:
            return import_students_csv(handle, default_password="TestPass123!")

    def test_summary_matches_the_documented_outcome(self):
        result = self._run()
        self.assertEqual(
            result["summary"],
            {"total": 21, "created": 17, "skipped": 0, "updated": 0, "failed": 4},
        )

    def test_the_right_rows_fail_with_the_right_reasons(self):
        result = self._run()
        failures = {
            row.line: row.messages[0]
            for row in result["rows"]
            if row.action == "failed"
        }
        self.assertEqual(set(failures), {11, 12, 14, 18})
        self.assertIn("username is required", failures[11])
        self.assertIn("duplicate email", failures[12])
        self.assertIn("duplicate username", failures[14])
        self.assertIn("email is required", failures[18])

    def test_recoverable_rows_import_with_warnings(self):
        result = self._run()
        warned = {row.line for row in result["rows"] if row.messages and row.action == "created"}
        self.assertEqual(warned, {7, 8, 9})

    def test_only_valid_rows_reach_the_database(self):
        self._run()
        self.assertEqual(User.objects.count(), 17)
        self.assertEqual(Student.objects.count(), 17)
        self.assertFalse(User.objects.filter(username="test011").exists())


class StudentImportViewTests(ImportTestCase):
    """The admin-only upload page at /students/import/."""

    def setUp(self):
        super().setUp()
        self.url = reverse("student_import")
        self.admin = User.objects.create_user(
            username="admin1", email="admin1@example.com",
            password="TestPass123!", role=User.Role.ADMIN,
        )
        self.student = User.objects.create_user(
            username="student1", email="student1@example.com",
            password="TestPass123!", role=User.Role.STUDENT,
        )

    def test_anonymous_user_is_denied(self):
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_student_is_denied(self):
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_admin_can_open_the_page(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_admin_upload_creates_students(self):
        self.client.force_login(self.admin)
        upload = SimpleUploadedFile(
            "students.csv",
            (CSV_HEADER + f"s9,Ada,Lovelace,ada@example.com,,{PROGRAM_NAME},100,,\n").encode("utf-8"),
            content_type="text/csv",
        )

        response = self.client.post(
            self.url,
            {"csv_file": upload, "default_password": "TestPass123!", "skip_duplicates": "on"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username="s9").exists())
        self.assertEqual(response.context["summary"]["created"], 1)

    def test_header_error_is_shown_as_a_form_error(self):
        self.client.force_login(self.admin)
        upload = SimpleUploadedFile(
            "bad.csv", b"first_name,last_name\nAda,Lovelace\n", content_type="text/csv"
        )

        response = self.client.post(self.url, {"csv_file": upload})

        self.assertEqual(response.status_code, 200)
        self.assertIn("csv_file", response.context["form"].errors)
        self.assertEqual(User.objects.count(), 2)
        self.assertFalse(User.objects.filter(first_name="Ada").exists())

    def test_non_csv_extension_is_rejected(self):
        self.client.force_login(self.admin)
        upload = SimpleUploadedFile(
            "students.txt", b"username,first_name\n", content_type="text/plain"
        )

        response = self.client.post(self.url, {"csv_file": upload})

        self.assertEqual(response.status_code, 200)
        self.assertIn("csv_file", response.context["form"].errors)


class ImportStudentsCommandTests(ImportTestCase):
    """
    The import_students management command — the non-browser route into
    the same import engine. --dry-run is the interesting case: it must
    report what would happen while writing nothing.
    """

    def _write_csv(self, rows, header=CSV_HEADER):
        handle = tempfile.NamedTemporaryFile(
            "w", suffix=".csv", delete=False, encoding="utf-8", newline=""
        )
        handle.write(header + "".join(rows))
        handle.close()
        self.addCleanup(Path(handle.name).unlink, missing_ok=True)
        return handle.name

    def test_command_imports_rows(self):
        path = self._write_csv(["s1,Ada,Lovelace,ada@example.com,,,100,,\n"])
        out = io.StringIO()

        call_command("import_students", file=path, password="TestPass123!", stdout=out)

        self.assertTrue(User.objects.filter(username="s1").exists())
        self.assertIn("1 created", out.getvalue())

    def test_dry_run_reports_but_writes_nothing(self):
        path = self._write_csv(["s1,Ada,Lovelace,ada@example.com,,,100,,\n"])
        out = io.StringIO()

        call_command(
            "import_students",
            file=path,
            password="TestPass123!",
            dry_run=True,
            stdout=out,
        )

        self.assertFalse(User.objects.filter(username="s1").exists())
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(Student.objects.count(), 0)
        output = out.getvalue()
        self.assertIn("DRY RUN", output)
        self.assertIn("1 created", output)

    def test_dry_run_rolls_back_a_larger_batch_too(self):
        rows = [
            f"s{n},First{n},Last{n},user{n}@example.com,,{PROGRAM_NAME},100,,\n"
            for n in range(1, 26)
        ]
        path = self._write_csv(rows)
        out = io.StringIO()

        call_command(
            "import_students",
            file=path,
            password="TestPass123!",
            dry_run=True,
            stdout=out,
        )

        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(Student.objects.count(), 0)
        self.assertIn("25 created", out.getvalue())

    def test_update_flag_refreshes_existing_users(self):
        User.objects.create_user(
            username="s1", email="ada@example.com", password="TestPass123!",
            first_name="Old", last_name="Name", role=User.Role.STUDENT,
        )
        path = self._write_csv([f"s1,Ada,Lovelace,ada@example.com,,{PROGRAM_NAME},200,,\n"])

        call_command(
            "import_students",
            file=path,
            password="TestPass123!",
            update=True,
            stdout=io.StringIO(),
        )

        user = User.objects.get(username="s1")
        self.assertEqual(user.first_name, "Ada")
        self.assertEqual(user.student_profile.level, "200")

    def test_bad_header_raises_command_error(self):
        path = self._write_csv(
            ["Ada,Lovelace,ada@example.com\n"], header="first_name,last_name,email\n"
        )

        with self.assertRaises(CommandError):
            call_command("import_students", file=path, stdout=io.StringIO())

        self.assertEqual(User.objects.count(), 0)

    def test_generated_password_is_printed_and_usable(self):
        path = self._write_csv(["s1,Ada,Lovelace,ada@example.com,,,100,,\n"])
        out = io.StringIO()

        call_command("import_students", file=path, stdout=out)

        prefix = "Generated password for all imported students:"
        output = out.getvalue()
        self.assertIn(prefix, output)

        generated = output.split(prefix)[1].strip().splitlines()[0].strip()
        self.assertTrue(User.objects.get(username="s1").check_password(generated))
