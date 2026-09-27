# Closed loans seeded without save() can keep delay_days at 0.

from datetime import datetime
from zoneinfo import ZoneInfo

from django.db import migrations
from django.db.models import Q

PARIS = ZoneInfo("Europe/Paris")


def _europe_paris_date(value):
    """Calendar date of a borrow timestamp in Europe/Paris.

    Naive values already store a wall-clock date, so ``.date()`` is used
    as-is. Aware values are converted to Europe/Paris before taking the date.
    """
    if value is None or not isinstance(value, datetime):
        return None
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        return value.date()
    return value.astimezone(PARIS).date()


def backfill_closed_borrow_delay_days(apps, schema_editor):
    """Fill delay_days on closed loans that were stored as 0 or null.

    A closed loan keeps the delay saved when it was returned. Rows inserted
    without ``BorrowRecord.save()`` can stay at 0 even when the Paris close
    date is after the Paris due date. Only those rows change, and only
    ``delay_days`` is written, so ``save()`` and auto-updated timestamps do
    not run. Open loans and closed loans that already have a delay are left
    alone.
    """
    BorrowRecord = apps.get_model("book", "BorrowRecord")
    candidates = BorrowRecord.objects.filter(
        open_or_close=1,
        closed_at__isnull=False,
        end_day__isnull=False,
    ).filter(Q(delay_days=0) | Q(delay_days__isnull=True))

    pending = []
    for record in candidates.iterator():
        due = _europe_paris_date(record.end_day)
        closed = _europe_paris_date(record.closed_at)
        if due is None or closed is None or closed <= due:
            continue
        record.delay_days = (closed - due).days
        pending.append(record)
    if pending:
        BorrowRecord.objects.bulk_update(pending, ["delay_days"])


class Migration(migrations.Migration):

    dependencies = [
        ("book", "0038_borrowrecord_closed_at_nullable"),
    ]

    operations = [
        migrations.RunPython(
            backfill_closed_borrow_delay_days,
            migrations.RunPython.noop,
        ),
    ]
