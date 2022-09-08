import json
import time
from dataclasses import dataclass
from datetime import date
from typing import Protocol

import requests
import undetected_chromedriver
from bs4 import BeautifulSoup

from .models import Channel, News as NewsDB, Tag


@dataclass(slots=True)
class News:
    # url: str
    title: str
    body: str
    channel: str
    tags: list[str]
    date: date


class NotNewsElements(Exception):
    pass


class Parser(Protocol):
    def parse(self) -> list[News]:
        pass


class YandexParser:
    def __init__(self):
        self.url_page_news_list = "https://market.yandex.ru/partners/news"
        self.base_url_page_news = "https://market.yandex.ru"

    def parse(self) -> list[News]:
        news_list = list()
        html = self._get_source_page(self.url_page_news_list)
        news_element_list = self._parse_page_list_news(html)
        for news in news_element_list[:10]:
            url = f'{self.base_url_page_news}{news.find("a").get("href")}'
            title = news.find("div", class_="news-list__item-header").text
            news_date = news.find("time", class_="news-list__item-date").get("datetime").split("T")[0]
            body, tags = self._parse_page_news(url)
            news_list.append(
                News(title=title, body=body, channel="yandex", tags=[tag.strip() for tag in tags.split("#") if tag],
                     date=date.fromisoformat(news_date))
            )
        return news_list

    @staticmethod
    def _get_source_page(url) -> str:
        response = requests.get(url)
        return response.text

    @staticmethod
    def _parse_page_list_news(html: str) -> list:
        soup = BeautifulSoup(html, "lxml")
        news_element_list = soup.find("div", class_="news-list__group").find_all("div", class_="news-list__item")
        return news_element_list

    def _parse_page_news(self, url: str):
        html = self._get_source_page(url)
        soup = BeautifulSoup(html, "lxml")
        body = soup.find("div", class_="news-info__post-body").text
        tags = soup.find("div", class_="news-info__tags").text
        return body, tags


class OzonParser:
    def __init__(self):
        self.url_page_news_list = "https://seller.ozon.ru/news/"
        self.base_api_url_page_news = "https://seller.ozon.ru/content-api"
        self.base_url_page_news = "https://seller.ozon.ru"

    def parse(self) -> list[News]:
        news_list = []
        html = self._get_html_from_news_page(self.url_page_news_list)
        news_elements = self._get_links_title_tags_date(html)
        driver = undetected_chromedriver.Chrome()
        for element in news_elements:
            content = self._get_body_news(driver, element["link"])
            news_list.append(
                News(title=element["title"], body=content, channel="ozon",
                     tags=element["tags"], date=element["date"])
            )
        driver.close()
        driver.quit()
        return news_list

    @staticmethod
    def _get_body_news(driver, url: str):
        driver.get(url)
        time.sleep(1)
        json_content = driver.find_element("css selector", "body").text
        news = json.loads(json_content)
        return news["content"]

    def _get_links_title_tags_date(self, html: str) -> list[dict]:
        news = list()
        soup = BeautifulSoup(html, "lxml")
        news_element_list = soup.find_all("div", class_="news-card")
        if not news_element_list:
            raise NotNewsElements
        for news_element in news_element_list[:10]:
            tags = list()
            link = f'{self.base_api_url_page_news}{news_element.find("a", class_="news-card__link").get("href")}'
            title = news_element.find("h3", class_="news-card__title").text.strip()
            tag_elements = news_element.find_all("div", class_="news-card__mark")
            date_text = news_element.find("span", class_="news-card__date").text
            news_date = self._format_date(date_text)
            for tag_element in tag_elements:
                tags.append(tag_element.text.strip())
            news.append({"link": link, "title": title, "tags": tags, "date": news_date})
        return news

    @staticmethod
    def _get_html_from_news_page(url: str):
        driver = undetected_chromedriver.Chrome()
        driver.get(url)
        time.sleep(2)
        driver.find_element("css selector", "div.news-paging").find_element("css selector", "button").click()
        time.sleep(2)
        html = driver.page_source
        driver.close()
        driver.quit()
        return html

    @staticmethod
    def _format_date(date_text: str):
        month = {"января": 1, "февраля": 2, "марта": 3, "апреля": 4, "мая": 5, "июня": 6, "июля": 7, "августа": 8,
                 "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12}
        day, month_text = date_text.split()
        return date(year=2022, month=month[month_text.lower()], day=int(day))


def _get_news(*parsers: type[Parser]) -> list[News]:
    news = []
    for parser in parsers:
        news.extend(parser().parse())
    return news


def _get_channel(channel_name: str) -> Channel:
    try:
        channel = Channel.objects.get(name=channel_name)
    except Channel.DoesNotExist:
        channel = Channel.objects.create(name=channel_name)
    return channel


def _get_tag(tag_text: str) -> Tag:
    try:
        tag = Tag.objects.get(tag_text=tag_text)
    except Tag.DoesNotExist:
        tag = Tag.objects.create(tag_text=tag_text)
    return tag


def save_news():
    news_list = _get_news(YandexParser, OzonParser)
    for news in news_list:
        channel = _get_channel(news.channel)
        tags = [_get_tag(tag_text) for tag_text in news.tags]
        news_object = NewsDB.objects.create(
            title=news.title,
            body=news.body,
            channel=channel,
            date=news.date
        )
        news_object.tags.add(*tags)
