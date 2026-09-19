# encoding=utf-8
import datetime

from pupa.scrape import Jurisdiction, Organization

from .bills import Oak_ParkBillScraper
from .events import Oak_ParkEventScraper
from .people import Oak_ParkPersonScraper


class Oak_Park(Jurisdiction):
    division_id = "ocd-division/country:us/state:il/place:oak_park"
    classification = "legislature"
    name = "Village of Oak Park"
    url = "https://www.oak-park.us/"
    scrapers = {
        "bills": Oak_ParkBillScraper,
        "events": Oak_ParkEventScraper,
        "people": Oak_ParkPersonScraper,
    }

    # Legistar's earliest records for Oak Park begin in late 2014.
    FIRST_YEAR = 2014

    @property
    def legislative_sessions(self):
        """
        Oak Park legislation is numbered by calendar year (e.g. RES 15-102
        for a resolution introduced in 2015), so each session covers a
        single calendar year.
        """
        this_year = datetime.datetime.now().year

        sessions = []
        for year in range(self.FIRST_YEAR, this_year + 1):
            sessions.append(
                {
                    "identifier": str(year),
                    "name": "{} Session".format(year),
                    "start_date": "{}-01-01".format(year),
                    "end_date": "{}-12-31".format(year),
                }
            )

        return sessions

    def get_organizations(self):
        org = Organization(
            name="President and Board of Trustees", classification="legislature"
        )

        org.add_post(label="Village President", role="Village President")
        org.add_post(label="Village Trustee", role="Village Trustee")

        org.add_source("https://oak-park.legistar.com/People.aspx", note="web")

        yield org
