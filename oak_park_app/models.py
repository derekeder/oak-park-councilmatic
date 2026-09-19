from django.conf import settings
from django.db import models
from councilmatic_core.models import Bill, Event, Person, Organization
from datetime import datetime
import pytz

app_timezone = pytz.timezone(settings.TIME_ZONE)


class OakParkBill(Bill):
    """
    Extend the base Bill model for city-specific functionality.
    Add any custom fields or methods specific to your city here.
    """

    class Meta:
        proxy = True

    def __str__(self):
        return self.friendly_name or self.identifier

    STATUS_LABELS = {
        "passage": "Passed",
        "failure": "Failed",
        "withdrawal": "Withdrawn",
        "deferral": "Tabled",
    }

    @property
    def inferred_status(self):
        action = self.current_action
        if not action or not action.classification:
            return None

        return self.STATUS_LABELS.get(action.classification[0], "Active")


class OakParkEvent(Event):
    """
    Extend the base Event model for city-specific functionality.
    Add any custom fields or methods specific to your city here.
    """
    
    class Meta:
        proxy = True


class OakParkPerson(Person):
    """
    Extend the base Person model for city-specific functionality.
    Add any custom fields or methods specific to your city here.
    """
    
    class Meta:
        proxy = True


class OakParkOrganization(Organization):
    """
    Extend the base Organization model for city-specific functionality.
    Add any custom fields or methods specific to your city here.
    """
    
    class Meta:
        proxy = True
