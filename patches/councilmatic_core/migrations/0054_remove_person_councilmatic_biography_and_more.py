from django.db import migrations


class Migration(migrations.Migration):
    """
    django-councilmatic's 5.x branch removed the `councilmatic_biography`
    and `headshot` fields from Person in models.py, but never shipped the
    corresponding migration (see the Person model at
    https://github.com/datamade/django-councilmatic/blob/5.x/councilmatic_core/models.py).

    Without this file, `manage.py migrate` fails because our own
    oak_park_app.0001_initial migration depends on a councilmatic_core
    migration that doesn't exist in the installed package. This file is
    copied into the installed councilmatic_core package at image build
    time (see Dockerfile) to fill that gap. Remove it once upstream ships
    an equivalent migration.
    """

    dependencies = [
        ("councilmatic_core", "0053_add_councilmatic_bio"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="person",
            name="councilmatic_biography",
        ),
        migrations.RemoveField(
            model_name="person",
            name="headshot",
        ),
    ]
