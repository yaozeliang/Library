# Closed loans keep the timestamp they already have. Open loans must not.

from django.db import migrations, models


def clear_closed_at_on_open_records(apps, schema_editor):
    """Drop close timestamps that auto_now wrote onto loans that are still open."""
    BorrowRecord = apps.get_model("book", "BorrowRecord")
    BorrowRecord.objects.exclude(open_or_close=1).update(closed_at=None)


class Migration(migrations.Migration):

    dependencies = [
        ("book", "0037_widen_borrowrecord_book"),
    ]

    operations = [
        migrations.AlterField(
            model_name="borrowrecord",
            name="closed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(
            clear_closed_at_on_open_records,
            migrations.RunPython.noop,
        ),
    ]
