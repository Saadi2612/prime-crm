from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Adds targeted DB indexes to resolve query-level bottlenecks:

    1. leadnote(lead_id, created_at DESC)
       Speeds up `get_latest_note` which does ORDER BY created_at DESC LIMIT 1
       per lead — without this index PostgreSQL scans the entire notes table.

    2. leadnote(next_follow_up)
       Speeds up `next_follow_up__date = today` filters used by `today-follow-ups/`
       and `stats/`. PostgreSQL can use a plain btree index on a DateTimeField even
       when filtering by the date component via __date lookup.

    3. lead(assigned_to_id, created_at DESC)
       Speeds up agent-scoped list queries which always filter by assigned_to
       and then order by -created_at.
    """

    dependencies = [
        ('leads', '0011_alter_leadnote_next_follow_up'),
    ]

    operations = [
        # Composite index: speeds up "latest note per lead" ORDER BY pattern
        migrations.AddIndex(
            model_name='leadnote',
            index=models.Index(
                fields=['lead', '-created_at'],
                name='leadnote_lead_created_idx',
            ),
        ),
        # Index on next_follow_up: speeds up date-range follow-up filters
        migrations.AddIndex(
            model_name='leadnote',
            index=models.Index(
                fields=['next_follow_up'],
                name='leadnote_follow_up_idx',
            ),
        ),
        # Composite index: speeds up agent-filtered lead list queries
        migrations.AddIndex(
            model_name='lead',
            index=models.Index(
                fields=['assigned_to', '-created_at'],
                name='lead_assigned_created_idx',
            ),
        ),
    ]
