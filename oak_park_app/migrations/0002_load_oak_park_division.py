from django.db import migrations

DIVISION_ID = "ocd-division/country:us/state:il/place:oak_park"
DIVISION_NAME = "Oak Park village"


def create_division(apps, schema_editor):
    Division = apps.get_model("core", "Division")

    if Division.objects.filter(id=DIVISION_ID).exists():
        return

    # Mirrors opencivicdata.core.models.division.DivisionManager.create,
    # which isn't available on the historical model apps.get_model returns.
    Division.objects.create(
        id=DIVISION_ID,
        name=DIVISION_NAME,
        country="us",
        subtype1="state",
        subid1="il",
        subtype2="place",
        subid2="oak_park",
    )


def remove_division(apps, schema_editor):
    Division = apps.get_model("core", "Division")
    Division.objects.filter(id=DIVISION_ID).delete()


class Migration(migrations.Migration):
    """
    Our Jurisdiction (oak_park.Oak_Park) references this division_id, and
    opencivicdata_jurisdiction has a FK to opencivicdata_division. Rather
    than loading the entire `manage.py loaddivisions us` dataset (tens of
    thousands of rows) just to satisfy that FK, create only the one
    division this project actually needs.
    """

    dependencies = [
        ("oak_park_app", "0001_initial"),
        ("core", "0009_auto_20241111_1450"),
    ]

    operations = [
        migrations.RunPython(create_division, remove_division),
    ]
