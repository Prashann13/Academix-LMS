"""
Bulk-import students from a CSV file.

Used by both the admin CSV upload view (students/views.py) and the
management command (students/management/commands/import_students.py),
so the import logic lives in exactly one place.

CSV format (header row required):
    username,first_name,last_name,email,phone_number,program,level,
    date_of_birth,address

    username      required, must be unique
    first_name    required
    last_name     required
    email         required, must be unique
    phone_number  optional
    program       optional, Program name (e.g. "B.Sc. Computer Science")
    level         optional, one of 100 / 200 / 300 / 400 (default 100)
    date_of_birth optional, YYYY-MM-DD
    address       optional free text

Efficiency choices for the 500-row case:
    * ONE password hash: every imported user gets the same (default or
      provided) password, so the expensive hasher runs once, not 500
      times. Hashing is deliberately the slowest part of an import.
    * Pre-fetched lookups: existing usernames/emails are loaded into
      sets and Program rows into a dict with a fixed handful of queries
      — instead of hitting the DB per row (1500+).
    * bulk_create: Users and Students are written with two bulk INSERTs
      instead of 1000 individual INSERTs.
    * Matric numbers are assigned in Python (STU/00001-style, continuing
      past the current maximum) so Student.save()'s per-row second query
      never runs.
    * @transaction.atomic: all rows commit together or not at all.
"""

import csv
import io
from datetime import datetime
from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.utils.crypto import get_random_string

from core.models import AcademicSession
from course.models import Program

from .models import Student

User = get_user_model()

REQUIRED_COLUMNS = ["username", "first_name", "last_name", "email"]
VALID_LEVELS = [choice[0] for choice in Student._meta.get_field("level").choices]
MATRIC_WIDTH = 5


class RowResult:
    """Per-row outcome so the UI/command can show exactly what happened."""

    def __init__(self, line, username, action, messages):
        self.line = line
        self.username = username
        self.action = action
        self.messages = messages


def _decode_bytes(data):
    """Decode raw CSV bytes, preferring utf-8-sig so Excel's BOM is stripped."""
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            return io.StringIO(data.decode(encoding))
        except UnicodeDecodeError:
            continue
    raise ValueError("CSV file is not UTF-8 or Latin-1 encoded")


def _decode(csv_file):
    """
    Accept a file-like object in binary or text mode, or a filesystem
    path, and return a text stream for csv.DictReader.

    The whole file is read into memory and the handle closed immediately,
    so no file stays open while the caller processes rows.
    """
    if hasattr(csv_file, "read"):
        chunk = csv_file.read()
        if isinstance(chunk, str):
            return io.StringIO(chunk)
        return _decode_bytes(chunk)
    return _decode_bytes(Path(csv_file).read_bytes())


def _parse_date(value):
    """Accept YYYY-MM-DD; returns None for blank or unparseable input."""
    value = (value or "").strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


@transaction.atomic
def import_students_csv(csv_file, default_password=None, skip_duplicates=True):
    """
    Import students from a CSV file.

    Args:
        csv_file:         file-like object or path (see _decode).
        default_password: password assigned to every created student.
                          If None, a random one is generated and returned
                          so the caller can surface it.
        skip_duplicates:  True  -> rows whose username or email already
                          exists are skipped. False -> existing users have
                          names/role and their Student record refreshed.

    Returns dict with keys:
        summary:           {total, created, skipped, updated, failed}
        rows:              list of RowResult, one per CSV data row
        generated_password: the password used when none was supplied
    """
    reader = csv.DictReader(_decode(csv_file))

    header_lower = [(h or "").strip().lower() for h in (reader.fieldnames or [])]
    missing = [c for c in REQUIRED_COLUMNS if c not in header_lower]
    if missing:
        raise ValueError("CSV is missing required column(s): " + ", ".join(missing))

    raw_rows = list(reader)

    usernames_in_file = [(r.get("username") or "").strip() for r in raw_rows]
    emails_in_file = [(r.get("email") or "").strip() for r in raw_rows]

    existing_users = {
        u.username: u
        for u in User.objects.filter(username__in=usernames_in_file)
    }
    email_owners = {
        e.lower(): un
        for e, un in User.objects.filter(email__in=emails_in_file)
        .values_list("email", "username")
    }
    existing_student_user_ids = set(
        Student.objects.filter(user__username__in=usernames_in_file)
        .values_list("user_id", flat=True)
    )
    program_lookup = {p.name.strip().lower(): p for p in Program.objects.all()}
    current_session = AcademicSession.objects.filter(is_current=True).first()

    generated_password = None
    if default_password:
        hashed = make_password(default_password)
    else:
        generated_password = get_random_string(length=12)
        hashed = make_password(generated_password)

    last_matric = (
        Student.objects.order_by("-id")
        .values_list("matric_number", flat=True)
        .first()
    )
    next_seq = 1
    if last_matric and last_matric.startswith("STU/"):
        try:
            next_seq = int(last_matric.split("/")[1]) + 1
        except (IndexError, ValueError):
            next_seq = 1

    seen_in_file = set()
    seen_emails = set()
    results = []
    new_pairs = []
    update_users = []
    update_students = []

    for line_no, row in enumerate(raw_rows, start=2):
        username = (row.get("username") or "").strip()
        first = (row.get("first_name") or "").strip()
        last = (row.get("last_name") or "").strip()
        email = (row.get("email") or "").strip()
        messages = []

        def fail(msg):
            results.append(RowResult(line_no, username or "(blank)", "failed", [msg]))

        if not username:
            fail("username is required")
            continue
        if not first or not last:
            fail("first_name and last_name are required")
            continue
        if not email or "@" not in email:
            fail("email is required and must be a valid address")
            continue
        if username in seen_in_file:
            fail("duplicate username inside the CSV file")
            continue
        if email.lower() in seen_emails:
            fail("duplicate email inside the CSV file")
            continue
        seen_in_file.add(username)
        seen_emails.add(email.lower())

        program = None
        program_raw = (row.get("program") or "").strip()
        if program_raw:
            program = program_lookup.get(program_raw.lower())
            if program is None:
                messages.append(f"unknown program '{program_raw}' — left blank")

        level = (row.get("level") or "").strip() or "100"
        if level not in VALID_LEVELS:
            messages.append(f"invalid level '{level}' — defaulted to 100")
            level = "100"

        dob = _parse_date(row.get("date_of_birth"))
        if (row.get("date_of_birth") or "").strip() and dob is None:
            messages.append("unparseable date_of_birth — left blank")

        address = (row.get("address") or "").strip()
        phone = (row.get("phone_number") or "").strip()

        existing_user = existing_users.get(username)
        email_taken_by_other = (
            email.lower() in email_owners
            and email_owners[email.lower()] != username
        )

        if existing_user or email_taken_by_other:
            if skip_duplicates:
                reason = (
                    "username already exists"
                    if existing_user
                    else "email already used by another user"
                )
                results.append(RowResult(line_no, username, "skipped", [reason]))
                continue

            if existing_user is None:
                results.append(
                    RowResult(line_no, username, "skipped",
                              ["email already used by another user"])
                )
                continue

            existing_user.first_name = first
            existing_user.last_name = last
            existing_user.role = User.Role.STUDENT
            update_users.append(existing_user)

            if existing_user.id in existing_student_user_ids:
                student = Student.objects.get(user_id=existing_user.id)
                student.program = program or student.program
                student.level = level
                student.date_of_birth = dob or student.date_of_birth
                student.address = address or student.address
                update_students.append(student)
                results.append(RowResult(line_no, username, "updated", messages))
            else:
                new_pairs.append((existing_user, Student(
                    user=existing_user,
                    program=program,
                    level=level,
                    session_admitted=current_session,
                    date_of_birth=dob,
                    address=address,
                    matric_number=f"STU/{next_seq:0{MATRIC_WIDTH}d}",
                )))
                next_seq += 1
                results.append(
                    RowResult(line_no, username, "updated",
                              messages + ["created missing Student profile"])
                )
            continue

        user = User(
            username=username,
            first_name=first,
            last_name=last,
            email=email,
            phone_number=phone,
            role=User.Role.STUDENT,
            password=hashed,
        )
        student = Student(
            program=program,
            level=level,
            session_admitted=current_session,
            date_of_birth=dob,
            address=address,
            matric_number=f"STU/{next_seq:0{MATRIC_WIDTH}d}",
        )
        new_pairs.append((user, student))
        next_seq += 1
        results.append(RowResult(line_no, username, "created", messages))

    ready_students = [s for u, s in new_pairs if s.user_id is not None]
    new_pairs = [(u, s) for u, s in new_pairs if s.user_id is None]
    if new_pairs:
        new_users = [u for u, s in new_pairs]
        User.objects.bulk_create(new_users)
        for user, student in new_pairs:
            student.user = user
        ready_students.extend(s for u, s in new_pairs)
    if ready_students:
        Student.objects.bulk_create(ready_students, batch_size=500)

    if update_users:
        User.objects.bulk_update(update_users, ["first_name", "last_name", "role"])
    if update_students:
        Student.objects.bulk_update(
            update_students, ["program", "level", "date_of_birth", "address"]
        )

    summary = {
        "total": len(raw_rows),
        "created": sum(1 for r in results if r.action == "created"),
        "skipped": sum(1 for r in results if r.action == "skipped"),
        "updated": sum(1 for r in results if r.action == "updated"),
        "failed": sum(1 for r in results if r.action == "failed"),
    }
    return {
        "summary": summary,
        "rows": results,
        "generated_password": generated_password,
    }
