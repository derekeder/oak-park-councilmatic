import os
from django.conf import settings
from django.shortcuts import render
from django.utils import timezone
from django.views.generic import DetailView, ListView, TemplateView

from councilmatic_core.models import Bill, Event, Person
from oak_park_app.models import OakParkBill, OakParkEvent, OakParkPerson


class IndexView(TemplateView):
    template_name = "home_page.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        last_meeting = OakParkEvent.most_recent_past_city_council_meeting()

        council_bills = OakParkBill.objects.none()
        recent_bills = OakParkBill.objects.none()

        if last_meeting:
            date_cutoff = last_meeting.local_start_time.date()

            council_bills = (
                OakParkBill.objects.filter(
                    actions__date=date_cutoff,
                    from_organization__name=settings.CITY_COUNCIL_NAME,
                )
                .prefetch_related("actions")
                .distinct()
            )
            recent_bills = (
                OakParkBill.objects.filter(actions__date__gt=date_cutoff)
                .prefetch_related("actions")
                .distinct()
                .order_by("-last_action_date")[:10]
            )

        context.update(
            {
                "bill_count": Bill.objects.count(),
                "event_count": Event.objects.count(),
                "person_count": Person.objects.count(),
                "last_council_meeting": last_meeting,
                "next_council_meeting": OakParkEvent.next_city_council_meeting(),
                "upcoming_committee_meetings": OakParkEvent.upcoming_committee_meetings(),
                "council_bills": council_bills,
                "recent_bills": recent_bills,
            }
        )
        return context


class BillListView(ListView):
    model = OakParkBill
    template_name = "bill_list.html"
    context_object_name = "bills"
    paginate_by = 25

    def get_queryset(self):
        return (
            OakParkBill.objects.prefetch_related("actions__organization")
            .order_by("-last_action_date", "-identifier")
        )


class BillDetailView(DetailView):
    model = OakParkBill
    template_name = "bill_detail.html"
    context_object_name = "bill"
    slug_field = "slug"

    def get_queryset(self):
        return super().get_queryset().prefetch_related(
            "actions__organization",
            "sponsorships__person",
            "sponsorships__organization",
            "documents__links",
            "sources",
        )


class EventListView(ListView):
    model = OakParkEvent
    template_name = "event_list.html"
    context_object_name = "events"
    paginate_by = 25

    def get_queryset(self):
        return (
            OakParkEvent.objects.select_related("location")
            .prefetch_related("participants")
            .order_by("-start_time")
        )


class EventDetailView(DetailView):
    model = OakParkEvent
    template_name = "event_detail.html"
    context_object_name = "event"
    slug_field = "slug"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("location")
            .prefetch_related(
                "participants",
                "agenda__related_entities__bill__councilmatic_bill",
                "documents__links",
                "sources",
            )
        )


class PersonListView(ListView):
    model = OakParkPerson
    template_name = "person_list.html"
    context_object_name = "people"
    paginate_by = 50

    def get_queryset(self):
        return OakParkPerson.objects.order_by("name")


class PersonDetailView(DetailView):
    model = OakParkPerson
    template_name = "person_detail.html"
    context_object_name = "person"
    slug_field = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        person = self.object

        context["sponsored_legislation"] = OakParkBill.objects.filter(
            sponsorships__person=person, sponsorships__primary=True
        ).order_by("-last_action_date")[:10]

        membership = person.latest_council_membership
        if membership:
            context["council_membership"] = membership
            context["council_term_active"] = membership.end_date_dt > timezone.now()

        return context


def robots_txt(request):
    """Serve robots.txt file with crawling permissions based on environment."""
    return render(
        request,
        "robots.txt",
        {"ALLOW_CRAWL": os.getenv("ALLOW_CRAWL", "False").lower() == "true"},
        content_type="text/plain",
    )


def page_not_found(request, exception, template_name="404.html"):
    """Custom 404 error handler."""
    return render(request, template_name, status=404)


def server_error(request, template_name="500.html"):
    """Custom 500 error handler."""
    return render(request, template_name, status=500)
