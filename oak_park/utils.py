from urllib.parse import quote


def clean_url(url):
    """
    Legistar-hosted file URLs sometimes include unencoded characters (e.g.,
    literal spaces in uploaded filenames), which fail pupa's strict URI
    validation. `safe` excludes '%' so already-encoded URLs aren't
    double-encoded.
    """
    return quote(url, safe="%/:?&=#")
