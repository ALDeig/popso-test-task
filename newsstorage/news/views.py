from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from pydantic import ValidationError

from .services import NewsFilters, get_news_by_filters


@csrf_exempt
def get_news(request: HttpRequest):
    try:
        filters = NewsFilters.parse_raw(request.body.decode())
    except ValidationError:
        return JsonResponse({"success": False, "message": "ValidationError"})
    news = get_news_by_filters(filters)
    return JsonResponse({"success": True, "items": list(news)})
