import os
from django.shortcuts import render
from django.views.generic import DetailView, ListView, TemplateView

from councilmatic_core.models import Bill, Event, Person
from oak_park_app.models import OakParkBill, OakParkEvent


class IndexView(TemplateView):
    template_name = "home_page.html"
    
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            "bill_count": Bill.objects.count(),
            "event_count": Event.objects.count(),
            "person_count": Person.objects.count(),
        })
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
