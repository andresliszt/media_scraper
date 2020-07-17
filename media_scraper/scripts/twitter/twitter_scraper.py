# -*- coding: utf-8 -*-
"""Scrapping de twitter."""
import json
import re

import requests
from elastinga.schemas import TwitterPosts
from lxml.etree import ParserError  # pylint: disable=no-name-in-module
from requests_html import HTML

from media_scraper import logger
from media_scraper.scripts.twitter.utils import TwitterPostSerializer
from media_scraper.scripts.utils import ProxiesRequests

BASE_TWITTER_API_URL_HASHTAG = "https://twitter.com/i/search/timeline?f=tweets&vertical=default&q={}&src=tyah&reset_error_state=false&"

BASE_TWITTER_API_URL_USER = (
    "https://twitter.com/i/profiles/show/{}/timeline/tweets?"
)

AFTER_PART = "include_available_features=1&include_entities=1&include_new_items_bar=true"

HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "https://twitter.com/{}",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8",
    "X-Twitter-Active-User": "yes",
    "X-Requested-With": "XMLHttpRequest",
    "Accept-Language": "es",
}


# pylint: disable=anomalous-backslash-in-string

# TODO: Quizas los links incluirlos en la clase


class TwitterScrapy(ProxiesRequests):

    """Clase que maneja la extracción de datos de twitter."""

    @staticmethod
    def __generate_headers(key):
        HEADERS["Referer"] = HEADERS["Referer"].format(key)
        return HEADERS

    @staticmethod
    def __generate_url_hashtag(hashtag):

        hashtag = (
            "#" + hashtag if not hashtag.startswith("#") else hashtag
        )

        url = BASE_TWITTER_API_URL_HASHTAG.format(hashtag)

        return url

    @staticmethod
    def __generate_url_user(username):

        url = BASE_TWITTER_API_URL_USER.format(username)
        url = url + AFTER_PART
        return url

    def _gen_tweet(self, url, headers, date_limit, retry, params=None):
        """Generador que busca los posts en url de users o hashtags.

        Args:
            url: Links hacia la api de twitter de user o hashtags.
            headers: Headers de request http.
            params: Parámetros adicionales para la requests.
            date_limit: Fecha límite donde buscar posts.
            retry: Si por alguna razón falla una requests, intenta de nuevo
                   tantas veces como sea este valor.

        Returns:
            Lista vacia si es que no hay resultados

        Yields:
            Diccionarios con información de cada posts

        """

        session = self._requests
        proxy = next(self.proxies_pool)

        if not params:
            params = {}

        logger.info(
            "Haciendo requests para `url` desde el `proxy`",
            url=url,
            proxy=proxy,
        )

        response = session.get(
            url, headers=headers, params=params, proxies={"http": proxy}
        )

        while True:
            try:
                response.raise_for_status()
                response = response.json()
                html = HTML(
                    html=response["items_html"],
                    url="bunk",
                    default_encoding="utf-8",
                )
                tweets = []
                for tweet, profile in zip(
                    html.find(".stream-item"),
                    html.find(".js-profile-popup-actionable"),
                ):
                    try:
                        tweets.append(
                            TwitterPostSerializer(tweet, profile)
                        )
                    except IndexError:
                        continue

                last_tweet = html.find(".stream-item")[-1].attrs[
                    "data-item-id"
                ]
                for tweet in tweets:
                    if date_limit and tweet.date <= date_limit:
                        break
                    tweet.text = re.sub(
                        r"(\S)http", "\g<1> http", tweet.text, 1
                    )
                    tweet.text = re.sub(
                        r"(\S)pic\.twitter",
                        "\g<1> pic.twitter",
                        tweet.text,
                        1,
                    )
                    yield tweet

                params = {"max_position": last_tweet}

                proxy = next(self.proxies_pool)
                logger.info(
                    "Haciendo requests para `url` desde el `proxy` desde `from_tweet`",
                    url=url,
                    proxy=proxy,
                    from_tweet=params["max_position"],
                )
                response = session.get(
                    url,
                    params=params,
                    headers=headers,
                    proxies={"http": proxy},
                )

            except ParserError:
                break

            except (
                requests.exceptions.Timeout,
                requests.exceptions.HTTPError,
                requests.exceptions.ConnectionError,
                requests.exceptions.ChunkedEncodingError,
                json.JSONDecodeError,
            ) as e:
                logger.error(
                    "Error mientras se hace el requests para la url",
                    url=url,
                    error=e,
                )

                if retry > 0:
                    logger.info("Re intentando para url", url=url)
                    yield from self._gen_tweet(
                        url=url,
                        headers=headers,
                        params=params,
                        date_limit=date_limit,
                        retry=retry - 1,
                    )

                return []

    def scrape_user_posts(
        self, username, params=None, date_limit=None, retry=5
    ):
        """Extrae posts dado un username.

        Args:
            username: Nombre del usario de twitter.

            Argumentos adicionales corresponden al método
            `~TwitterScrapy._gen_tweet`.

        Yields:
            Diccionarios con información de los posts del usuario.

        """
        url = self.__generate_url_user(username)
        headers = self.__generate_headers(username)
        yield from self._gen_tweet(
            url=url,
            headers=headers,
            params=params,
            date_limit=date_limit,
            retry=retry,
        )

    def scrape_hashtag_posts(
        self, hashtag, params=None, date_limit=None, retry=5
    ):
        """Extrae posts dado un hashtag.

        Args:
            hashtag: Hashtag target para buscar posts.

            Argumentos adicionales corresponden al método
            `~TwitterScrapy._gen_tweet`.

        Yields:
            Diccionarios con información de los posts asociados al hashtag.

        """
        url = self.__generate_url_hashtag(hashtag)
        headers = self.__generate_headers(hashtag)
        yield from self._gen_tweet(
            url=url,
            headers=headers,
            params=params,
            date_limit=date_limit,
            retry=retry,
        )

    def user_posts_to_es(self, username, **kwargs):
        """Graba los posts de un usuario en elasticsearch.

        Args:
            username: Nombre del usario de twitter.

        """

        for tweet in self.scrape_user_posts(username, **kwargs):
            values = tweet.__dict__
            values["username_timeline"] = username
            TwitterPosts(**values).save()

    def hashtag_posts_to_es(self, hashtag, **kwargs):
        """Graba los posts asociados a hashtag en elasticsearch.

        Args:
            hashtag: Hashtag target para buscar posts.

        """

        for tweet in self.scrape_hashtag_posts(hashtag, **kwargs):
            values = tweet.__dict__
            TwitterPosts(**values).save()
