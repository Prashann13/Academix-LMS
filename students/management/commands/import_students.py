"""
Management command wrapper around students/services.import_students_csv.

Usage:
    python manage.py import_students --file path/to/students.csv
    python manage.py import_students --file students.csv --password Changeme123!
    python manage.py import_students --file students.csv --update
    python manage.py import_students --file students.csv --dry-run

Why a command as well as the web view:
    * Works over SSH/CI where a browser isn't available.
    * --dry-run lets you validate a file against the real database
      without writing anything (the transaction is rolled back).
    * Easier to schedule (cron / Task Scheduler) for nightly syncs.
"""

from django.core.management.base import BaseCommand, CommandError

from students.services import import_students_csv


class Command(BaseCommand):
    help = "Bulk-import student accounts from a CSV file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file", required=True,
            help="Path to the CSV file (header row required).",
        )
        parser.add_argument(
            "--password", default=None,
            help="Password assigned to all imported students. "
                 "If omitted, a random one is generated and printed ONCE.",
        )
        parser.add_argument(
            "--update", action="store_true",
            help="Update existing users instead of skipping duplicate "
                 "username/email rows.",
        )
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Parse and validate the file, then roll back — nothing "
                 "is written to the database.",
        )

    def handle(self, *args, **options):
        from django.db import transaction

        path = options["file"]

        try:
            with transaction.atomic():
                result = import_students_csv(
                    path,
                    default_password=options["password"],
                    skip_duplicates=not options["update"],
                )
                if options["dry_run"]:
                    transaction.set_rollback(True)
        except ValueError as e:
            raise CommandError(str(e))

        s = result["summary"]

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("DRY RUN — all changes rolled back."))

        self.stdout.write(self.style.SUCCESS(
            f"Import summary: {s['total']} total, {s['created']} created, "
            f"{s['updated']} updated, {s['skipped']} skipped, {s['failed']} failed."
        ))

        if result["generated_password"]:
            self.stdout.write(self.style.NOTICE(
                f"Generated password for all imported students: "
                f"{result['generated_password']}"
            ))

        for r in result["rows"]:
            if r.action in ("skipped", "failed") or r.messages:
                style = (
                    self.style.ERROR if r.action == "failed"
                    else self.style.WARNING if r.action == "skipped"
                    else self.style.NOTICE
                )
                self.stdout.write(style(
                    f"  line {r.line}: {r.username} -> {r.action}"
                    + (f" ({'; '.join(r.messages)})" if r.messages else "")
                ))
