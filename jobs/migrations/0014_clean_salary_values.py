import re

from django.db import migrations


def clean_salary(apps, schema_editor):
    """Эски маалыматтардагы '30к' сыяктуу текст маанилерди санга айландыруу."""
    Job = apps.get_model('jobs', 'Job')
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SELECT id, salary FROM jobs_job")
        rows = cursor.fetchall()
    for pk, raw in rows:
        if raw is None or isinstance(raw, int):
            continue
        text = str(raw).lower().replace(' ', '')
        digits = re.sub(r'\D', '', text)
        value = int(digits) if digits else None
        if value is not None and ('к' in text or 'k' in text) and value < 1000:
            value *= 1000
        Job.objects.filter(pk=pk).update(salary=value)


class Migration(migrations.Migration):
    dependencies = [
        ('jobs', '0013_alter_job_options_alter_job_category_and_more'),
    ]

    operations = [
        migrations.RunPython(clean_salary, migrations.RunPython.noop),
    ]
