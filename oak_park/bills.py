import datetime

from legistar.bills import LegistarAPIBillScraper
from pupa.scrape import Bill, Scraper, VoteEvent
from pupa.utils import _make_pseudo_id


class Oak_ParkBillScraper(LegistarAPIBillScraper, Scraper):
    BASE_URL = "https://webapi.legistar.com/v1/oak-park"
    BASE_WEB_URL = "https://oak-park.legistar.com"
    TIMEZONE = "America/Chicago"

    VOTE_OPTIONS = {
        "ayes": "yes",
        "nays": "no",
        "present": "abstain",
        "absent": "absent",
        "abstained": "abstain",
        "recused": "abstain",
        "by phone": "abstain",
        None: "abstain",
    }

    def session(self, action_date):
        return str(action_date.year)

    def sponsorships(self, matter_id):
        for i, sponsor in enumerate(self.sponsors(matter_id)):
            sponsor_name = sponsor["MatterSponsorName"].strip()

            # Sponsors are either the body itself (e.g., the Board sponsoring
            # its own resolution) or a member of Village staff.
            entity_type = "organization" if sponsor.get("MatterSponsorBodyId") else "person"

            yield {
                "primary": i == 0,
                "classification": "Primary" if i == 0 else "Regular",
                "name": sponsor_name,
                "entity_type": entity_type,
            }

    def actions(self, matter_id):
        old_action = None
        for action in self.history(matter_id):
            action_description = action["MatterHistoryActionName"].strip()
            action_date = action["MatterHistoryActionDate"]
            responsible_org = action["MatterHistoryActionBodyName"].strip()

            if not all((action_date, action_description, responsible_org)):
                continue

            action_date = self.toTime(action_date).date()

            bill_action = {
                "description": action_description,
                "date": action_date,
                "organization": {"name": responsible_org},
                "classification": ACTION_CLASSIFICATION.get(action_description.lower()),
            }

            if bill_action == old_action:
                continue
            old_action = bill_action

            if (
                action["MatterHistoryEventId"] is not None
                and action["MatterHistoryRollCallFlag"] is not None
                and action["MatterHistoryPassedFlag"] is not None
            ):
                result = "pass" if action["MatterHistoryPassedFlag"] else "fail"
                votes = (result, self.votes(action["MatterHistoryId"]))
            else:
                votes = (None, [])

            yield bill_action, votes

    def scrape(self, window=28):
        """
        By default, scrape board reports updated in the last 28 days.
        Pass a window of 0 to scrape all legislation.
        """
        if float(window):
            n_days_ago = datetime.datetime.utcnow() - datetime.timedelta(float(window))
            matters = self.matters(n_days_ago)
        else:
            matters = self.matters()

        for matter in matters:
            matter_id = matter["MatterId"]
            date = matter["MatterIntroDate"]
            title = matter["MatterTitle"]
            identifier = matter["MatterFile"]

            if not all((date, title, identifier)):
                continue

            bill_session = self.session(self.toTime(date))

            bill = Bill(
                identifier=identifier,
                legislative_session=bill_session,
                title=title,
                classification=None,
                from_organization={"name": matter["MatterBodyName"]},
            )

            legistar_api = self.BASE_URL + "/matters/{0}".format(matter_id)
            bill.add_source(legistar_api, note="api")

            legistar_web = matter.get("legistar_url")
            if legistar_web:
                bill.add_source(legistar_web, note="web")

            for action, vote in self.actions(matter_id):
                act = bill.add_action(**action)

                if action["description"].lower() == "referred":
                    body_name = matter["MatterBodyName"]
                    act.add_related_entity(
                        body_name,
                        "organization",
                        entity_id=_make_pseudo_id(name=body_name),
                    )

                result, votes = vote
                if result:
                    vote_event = VoteEvent(
                        legislative_session=bill.legislative_session,
                        motion_text=action["description"],
                        organization=action["organization"],
                        classification=None,
                        start_date=action["date"],
                        result=result,
                        bill=bill,
                    )

                    vote_event.add_source(legistar_web or legistar_api)
                    vote_event.add_source(legistar_api + "/histories")

                    for vote in votes:
                        try:
                            raw_option = vote["VoteValueName"].lower()
                        except AttributeError:
                            raw_option = None
                        clean_option = self.VOTE_OPTIONS.get(raw_option, "abstain")
                        vote_event.vote(clean_option, vote["VotePersonName"].strip())

                    yield vote_event

            for sponsorship in self.sponsorships(matter_id):
                bill.add_sponsorship(**sponsorship)

            for topic in self.topics(matter_id):
                bill.add_subject(topic["MatterIndexName"].strip())

            for attachment in self.attachments(matter_id):
                if attachment["MatterAttachmentName"] and attachment[
                    "MatterAttachmentShowOnInternetPage"
                ]:
                    bill.add_document_link(
                        attachment["MatterAttachmentName"],
                        attachment["MatterAttachmentHyperlink"].strip(),
                        media_type="application/pdf",
                    )

            bill.extras = {"local_classification": matter["MatterTypeName"]}

            matter_version_value = matter["MatterVersion"]
            text = self.text(matter_id, matter_version_value)

            if text:
                if text["MatterTextPlain"]:
                    bill.extras["plain_text"] = text["MatterTextPlain"]

                if text["MatterTextRtf"]:
                    bill.extras["rtf_text"] = text["MatterTextRtf"].replace("\u0000", "")

            yield bill


# Defined according to OCD standard here:
# https://github.com/opencivicdata/python-opencivicdata/blob/master/opencivicdata/common.py
ACTION_CLASSIFICATION = {
    "adopted": "passage",
    "adopted as amended": "passage",
    "approved": "passage",
    "approved as amended": "passage",
    "denied": "failure",
    "failed": "failure",
    "tabled": "deferral",
    "withdrawn": "withdrawal",
    "referred": "referral-committee",
    "received and filed": "filing",
    "received": "receipt",
}
