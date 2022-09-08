from datetime import date
from enum import Enum

from pydantic import BaseModel

from .models import News


class FilterType(Enum):
    DATE = "date"
    TAG = "tag"
    CHANNEL = "channel"


class NewsFilters(BaseModel):
    type: FilterType
    value: str


def get_news_by_filters(filters: NewsFilters) -> list[dict]:
    values = ("title", "body", "channel", "tags", "date")
    match filters.type:
        case FilterType.DATE:
            news = News.objects.filter(date=date.fromisoformat(filters.value)).values(*values)
        case FilterType.CHANNEL:
            news = News.objects.filter(channel__name=filters.value).values(*values)
        case FilterType.TAG:
            news = News.objects.filter(tags__tag_text=filters.value).values(*values)
        case _:
            news = News.objects.values(*values)
    return news

