"""Query-string pagination shared by catalog and comment list views.

An out-of-range integer ``?page=`` is a 302 to ``page=<last page>``.
A non-integer or a number below 1 is a 302 that drops ``page`` (page 1).
Other parameters, such as search and orderby, stay on the URL.
An empty result set still has a first page, so ``?page=1`` renders
instead of redirecting again.
"""

from django.core.paginator import Paginator
from django.http import HttpResponseRedirect

# Catalog lists show five rows. Comment lists pass their own ``paginate_by``.
CATALOG_PAGE_SIZE = 5


def redirect_for_page(request, queryset, per_page=CATALOG_PAGE_SIZE):
    """Return a 302 when ``?page=`` is not a real page, otherwise ``None``.

    ``queryset`` is the filtered list before it is sliced into a page.
    A missing ``page`` parameter renders page 1 with no redirect.
    """
    if "page" not in request.GET:
        return None

    raw = request.GET.get("page")
    params = request.GET.copy()
    number = _positive_page(raw)
    if number is None:
        params.pop("page", None)
        return _redirect_unless_same(request, params)

    paginator = Paginator(queryset, per_page)
    # An empty list still exposes page 1 (allow_empty_first_page).
    last = paginator.num_pages or 1
    if number > last:
        params["page"] = str(last)
        return _redirect_unless_same(request, params)
    return None


def _positive_page(raw):
    """Return an integer page of 1 or more, or ``None`` when it is unusable."""
    text = str(raw).strip()
    try:
        number = int(text)
    except (TypeError, ValueError):
        return None
    if number < 1:
        return None
    return number


def _redirect_unless_same(request, params):
    query = params.urlencode()
    location = request.path
    if query:
        location = f"{location}?{query}"
    if location == request.get_full_path():
        return None
    return HttpResponseRedirect(location)
