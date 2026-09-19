import datetime

from legistar.events import LegistarAPIEventScraper
from pupa.scrape import Event, Scraper


class Oak_ParkEventScraper(LegistarAPIEventScraper, Scraper):
    BASE_URL = "https://webapi.legistar.com/v1/oak-park"
    WEB_URL = "https://oak-park.legistar.com"
    EVENTSPAGE = "https://oak-park.legistar.com/Calendar.aspx"
    TIMEZONE = "America/Chicago"

    def _status(self, event):
        status_name = event["EventAgendaStatusName"]

        if status_name.startswith("Final"):
            return "passed"
        elif status_name == "Draft":
            return "confirmed"
        elif status_name == "Canceled":
            return "cancelled"
        else:
            return "tentative"

    def scrape(self, window=28):
        """
        By default, scrape events updated in the last 28 days.
        Pass a window of 0 to scrape all events.
        """
        n_days_ago = None
        if window and float(window) != 0:
            n_days_ago = datetime.datetime.utcnow() - datetime.timedelta(float(window))

        for api_event, web_event in self.events(since_datetime=n_days_ago):
            body_name = api_event["EventBodyName"]

            location = api_event["EventLocation"] or "Not available"

            e = Event(
                body_name,
                start_date=api_event["start"],
                description="",
                location_name=location,
                status=self._status(api_event),
            )

            e.pupa_id = str(api_event["EventId"])
            e.extras = {"guid": api_event["EventGuid"]}

            legistar_api_url = self.BASE_URL + "/events/{0}".format(api_event["EventId"])
            e.add_source(legistar_api_url, note="api")

            for item in self.agenda(api_event):
                agenda_item = e.add_agenda_item(item["EventItemTitle"])

                if item["EventItemMatterFile"]:
                    agenda_item.add_bill(item["EventItemMatterFile"])

                if item["EventItemAgendaNumber"]:
                    agenda_number = item["EventItemAgendaNumber"]
                    agenda_item["notes"].append("Agenda number, {}".format(agenda_number))
                    agenda_item["extras"]["agenda_number"] = agenda_number

            e.add_participant(name=body_name, type="organization")

            if api_event["EventAgendaFile"]:
                e.add_document(
                    note="Agenda",
                    url=api_event["EventAgendaFile"],
                    media_type="application/pdf",
                )

            if api_event["EventMinutesFile"]:
                e.add_document(
                    note="Minutes",
                    url=api_event["EventMinutesFile"],
                    media_type="application/pdf",
                )

            e.add_source(web_event["Meeting Details"]["url"], note="web")

            yield e
