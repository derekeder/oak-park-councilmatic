from legistar.people import LegistarAPIPersonScraper
from pupa.scrape import Organization, Person, Scraper

TOP_LEVEL_BODY_NAME = "President and Board of Trustees"


class Oak_ParkPersonScraper(LegistarAPIPersonScraper, Scraper):
    BASE_URL = "https://webapi.legistar.com/v1/oak-park"
    WEB_URL = "https://oak-park.legistar.com"
    TIMEZONE = "America/Chicago"

    def _dedupe_offices(self, offices):
        """
        Legistar sometimes represents a correction to a term (e.g., an
        extended end date) as a brand new OfficeRecord that shares the same
        person, role, and start date as the original, instead of updating
        the original in place. Pupa's membership de-duplication only keys
        on start_date (not end_date), so importing both raises a
        DuplicateItemError. Keep only the most recently modified record for
        each (person, role, start_date) combination.
        """
        latest = {}
        for office in offices:
            key = (
                office["OfficeRecordFullName"],
                office["OfficeRecordTitle"],
                office["OfficeRecordStartDate"],
            )
            current = latest.get(key)
            if (
                current is None
                or office["OfficeRecordLastModifiedUtc"]
                > current["OfficeRecordLastModifiedUtc"]
            ):
                latest[key] = office

        return latest.values()

    def _get_or_create_person(self, office, members):
        name = office["OfficeRecordFullName"]

        if name in members:
            return members[name]

        p = Person(name)
        p.family_name = office["OfficeRecordLastName"]
        p.given_name = office["OfficeRecordFirstName"]

        person_api_url, person_web_url = self.person_sources_from_office(office)
        p.add_source(person_api_url, note="api")
        p.add_source(person_web_url, note="web")

        members[name] = p

        return p

    def scrape(self):
        bodies = list(self.bodies())

        (board,) = [body for body in bodies if body["BodyName"] == TOP_LEVEL_BODY_NAME]

        members = {}

        for office in self._dedupe_offices(self.body_offices(board)):
            p = self._get_or_create_person(office, members)

            p.add_term(
                office["OfficeRecordTitle"],
                "legislature",
                start_date=self.toDate(office["OfficeRecordStartDate"]),
                end_date=self.toDate(office["OfficeRecordEndDate"]),
            )

        for body in bodies:
            # The top-level board already got its own Organization above,
            # with classification="legislature".
            if not body["BodyActiveFlag"] or body["BodyId"] == board["BodyId"]:
                continue

            organization_name = body["BodyName"].strip()

            # Bills and events reference bodies by name (e.g., a matter
            # referred to "Finance Committee"), regardless of whether that
            # body currently has any tracked OfficeRecords. Always create
            # the organization so those references resolve, even when the
            # membership loop below yields no memberships.
            o = Organization(
                organization_name,
                classification="committee",
                parent_id={"name": TOP_LEVEL_BODY_NAME},
            )
            o.add_source(
                self.BASE_URL + "/bodies/{BodyId}".format(**body), note="api"
            )

            for office in self._dedupe_offices(self.body_offices(body)):
                p = self._get_or_create_person(office, members)

                p.add_membership(
                    organization_name,
                    role=office["OfficeRecordTitle"] or "Member",
                    start_date=self.toDate(office["OfficeRecordStartDate"]),
                    end_date=self.toDate(office["OfficeRecordEndDate"]),
                )

            yield o

        for p in members.values():
            yield p
