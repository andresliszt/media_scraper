# -*- coding: utf-8 -*-
"""Scrapping oficial usando requests."""
import datetime
import json
import urllib

import requests

from media_scraper import logger
from media_scraper.scripts.instagram.utils import (
    InstagramPostsSerializer,
)
from media_scraper.scripts.instagram.utils import OpenUserPost
from media_scraper.scripts.instagram.utils import PostComment
from media_scraper.scripts.instagram.utils import UserTimeLinePost
from media_scraper.scripts.utils import ProxiesRequests

# TODO: ACORTAR!!!!!!!!!!!!!!!!!!!


BASE_INSTAGRAM_API_URL_HASHTAG = (
    "https://www.instagram.com/explore/tags/%s/?__a=1&max_id=%s"
)

USER_INFO_BY_ID = "https://i.instagram.com/api/v1/users/%s/info/"

USER_POSTS = "https://www.instagram.com/graphql/query/?query_hash=42323d64886122307be10013ad2dcc44&variables=%s"

USER_ACCOUNT = "https://www.instagram.com/%s/?__a=1"

POST_COMMENTS_LINK = "https://www.instagram.com/graphql/query/?query_hash=97b41c52301f77ce508f55e66d17620e&variables=%s"

HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "User-Agent": "Instagram 126.0.0.25.121 Android (23/6.0.1; 320dpi; 720x1280;\
         samsung; SM-A310F; a3xelte; samsungexynos7580; en_GB; 110937453)",
    "X-Requested-With": "XMLHttpRequest",
    "Accept-Language": "es-CL",
}


INSTAGRAM_DAYS_RANGE_HASHTAG = datetime.date.today() - datetime.timedelta(
    days=7
)
"""Dias hacia atras donde se buscará por hashtag"""


class ScrapyInstagram(ProxiesRequests):

    """Clase que realiza requests a la API de Instagram.

    Por ahora están soportados:
        1 - Obtener información de usuario por id
        2 - Obtener información de usuario por username
        3 - Obtener Posts asociados a un hashtag
        4 - Obtener todos los posts de un usuario pariticular
        5 - Obtener todos los comentarios de un post

    """

    # TODO: Hace un decorador para los generadores
    # TODO: Revisar los parametros counts

    @staticmethod
    def __generate_hashtag_api_link(hashtag: str, end_cursor: str):
        return BASE_INSTAGRAM_API_URL_HASHTAG % (
            urllib.parse.quote_plus(str(hashtag)),
            urllib.parse.quote_plus(str(end_cursor)),
        )

    @staticmethod
    def __generate_user_name_link_by_id(user_id: int):
        return USER_INFO_BY_ID % urllib.parse.quote_plus(str(user_id))

    @staticmethod
    def __generate_user_profile_link_by_username(username):
        return USER_ACCOUNT % urllib.parse.quote_plus(username)

    @staticmethod
    def __generate_user_posts_link(variables):
        return USER_POSTS % urllib.parse.quote_plus(
            json.dumps(variables, separators=(",", ":"))
        )

    @staticmethod
    def __generate_post_comments_link(variables):
        return POST_COMMENTS_LINK % urllib.parse.quote_plus(
            json.dumps(variables, separators=(",", ":"))
        )

    @staticmethod
    def __make_request(session, url: str, proxy: str, timeout: int):

        proxies = {"http": proxy} if proxy else None
        response = session.get(
            url, headers=HEADERS, proxies=proxies, timeout=timeout
        )
        response.raise_for_status()

        return response

    def _get_user_by_id(self, user_id: int, proxy=None, timeout=50):
        session = self._requests
        url = self.__generate_user_name_link_by_id(user_id)
        logger.info("Obteniendo info del usuario con `id`", id=user_id)
        try:
            response = self.__make_request(session, url, proxy, timeout)
            return response

        except (
            requests.exceptions.HTTPError,
            requests.exceptions.Timeout,
            json.JSONDecodeError,
        ) as e:
            logger.error(
                "Error en la requests para el `user_id`",
                user_id=user_id,
                error=e,
            )
            return None

    def _get_user_by_username(self, username, proxy=None, timeout=50):
        session = self._requests
        url = self.__generate_user_profile_link_by_username(username)
        logger.info(
            "Obteniendo info del usuario con `username`",
            username=username,
        )
        try:
            response = self.__make_request(session, url, proxy, timeout)

        except (
            requests.exceptions.HTTPError,
            requests.exceptions.Timeout,
            json.JSONDecodeError,
        ) as e:
            logger.error(
                "Error en la requests para el `username`",
                username=username,
                error=e,
            )
            return None

        return response

    def get_user_by_id(self, user_id, timeout=50) -> dict:
        """Obtiene json ordenado con info. de usuario vía id.

        Args:
            user_id : Identificador del usuario
            timeout: Tiempo de espera para la response.

        Returns:
            Si el id es válido, entrega la información del usuario
                como diccionario. Si no, retorna `None`.

        """
        proxy = next(self.proxies_pool)
        response = self._get_user_by_id(
            user_id=user_id, proxy=proxy, timeout=timeout
        )
        if response:
            return response["user"]

        return {}

    def get_user_by_username(self, username, timeout=50):
        """Obtiene json ordenado con info. de usuario vía username.

        Args:
            username : Nombre de la cuenta de instagram
            timeout: Tiempo de espera para la response.

        Returns:
            Si el `username` es válido, entrega la información del usuario
                como diccionario. Si no, retorna `None`.

        """

        proxy = next(self.proxies_pool)
        response = self._get_user_by_username(
            username=username, proxy=proxy, timeout=timeout
        )
        if response:
            return response["graphql"]["user"]

        return {}

    def scrape_hashtag(
        self,
        hashtag: str,
        end_cursor="",
        *,
        retry=5,
        timeout=50,
        date_limit=None,
    ):
        """Generador con los posts asociados a un hashtag.

        Args:
            hashtag: hashtag a buscar. Puede ser con `#` o sin el.
            end_cursor: Este argumento es para navegar a través de la API
                        de Instagram. Sirve para paginar. Se genera
                        automático en esta API. Primera pagina corresponde
                        a el valor `end_cursor = ""`.
            retry: En caso de errores en la requests, se vuelve a intentar tantas
                   veces como valga este parámetro.
            timeout: Tiempo de espera para la response.
            date_limit: Fecha límite donde buscar los posts.

        Returns:
            Si no hay resultados en la búsqueda, se retorna una lista vacía.

        Yields:
            json con la información de cada post encontrado.

        """
        session = self._requests
        next_page = True
        while next_page:
            try:
                proxy = next(
                    self.proxies_pool
                )  # por cada requests, seteamos un ip diferente
                url = self.__generate_hashtag_api_link(
                    hashtag, end_cursor
                )
                logger.info(
                    "Haciendo requests para `url` desde el `proxy`",
                    url=url,
                    proxy=proxy,
                )

                response = self.__make_request(
                    session, url, proxy, timeout
                )

                response = response.json()

                try:
                    edge_hashtag_to_media = response["graphql"][
                        "hashtag"
                    ]["edge_hashtag_to_media"]

                except KeyError:
                    return []

                for edge in edge_hashtag_to_media["edges"]:
                    post = OpenUserPost(edge["node"])
                    yield post
                    if date_limit and (
                        post.time  # pylint: disable=no-member
                        <= date_limit
                    ):
                        break

                next_page = edge_hashtag_to_media["page_info"][
                    "has_next_page"
                ]

                end_cursor = edge_hashtag_to_media["page_info"][
                    "end_cursor"
                ]
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
                    yield from self.scrape_hashtag(
                        hashtag,
                        end_cursor=end_cursor,
                        retry=retry - 1,
                        timeout=timeout,
                        date_limit=date_limit,
                    )

                return []

    def scrape_user_posts(
        self,
        user_id: int,
        n_posts=50,
        end_cursor="",
        timeout=50,
        retry=5,
    ):
        """Generador con los posts de un usuario.

        Args:
            user_id: id del usuario
            n_posts: Cantidad de posts que se desean capturar.
            end_cursor: Este argumento es para navegar a través de la API
                        de Instagram. Sirve para paginar. Se genera
                        automático en esta API. Primera pagina corresponde
                        a el valor `end_cursor = ""`.
            timeout: Tiempo de espera para la response.
            date_limit: Fecha límite donde buscar los posts.

        Returns:
            Si no hay resultados en la búsqueda, se retorna una lista vacía.

        Yields:
            json con la información de cada post del usuario.

        """

        session = self._requests
        next_page = True
        post_counter = 0
        while next_page and (post_counter < n_posts):
            try:
                proxy = next(self.proxies_pool)

                variables = {
                    "id": str(user_id),
                    "first": str(n_posts),
                    "after": str(end_cursor),
                }

                url = self.__generate_user_posts_link(variables)
                response = self.__make_request(
                    session, url, proxy, timeout
                )
                response = response.json()

                try:

                    user = response["data"]["user"]

                    if not user:
                        # Ver cuando pasa este error
                        return []

                    edge_owner_to_timeline_media = user[
                        "edge_owner_to_timeline_media"
                    ]
                except KeyError:
                    return []

                for edge in edge_owner_to_timeline_media["edges"]:

                    post = UserTimeLinePost(edge["node"])

                    post_counter = +1

                    yield post

                end_cursor = edge_owner_to_timeline_media["page_info"][
                    "end_cursor"
                ]

                next_page = edge_owner_to_timeline_media["page_info"][
                    "has_next_page"
                ]

            except (
                requests.exceptions.Timeout,
                requests.exceptions.HTTPError,
                requests.exceptions.ConnectionError,
                requests.exceptions.ChunkedEncodingError,
                json.JSONDecodeError,
            ) as e:
                logger.error(
                    "Error mientras se hace el requests para la url",
                    error=e,
                )

                if retry > 0:
                    logger.info(
                        "Re intentando sacar posts, actualmente:",
                        cantidad_posts=post_counter,
                    )
                    yield from self.scrape_user_posts(
                        user_id=user_id,
                        n_posts=n_posts,
                        end_cursor=end_cursor,
                        retry=retry - 1,
                        timeout=timeout,
                    )

                return []

    def scrape_post_comments(
        self,
        post_id: int,
        end_cursor="",
        retry=5,
        timeout=50,
        n_comments=50,
    ):

        session = self._requests

        post_code = InstagramPostsSerializer.get_code_from_id(post_id)

        next_page = True

        counter = 0

        while next_page and (counter < n_comments):
            try:
                variables = {
                    "shortcode": str(post_code),
                    "first": "50",
                    "after": "" if not end_cursor else end_cursor,
                }

                url = self.__generate_post_comments_link(variables)

                proxy = next(self.proxies_pool)

                response = session.get(
                    url, proxies={"http": proxy}, headers=HEADERS,
                )

                response.raise_for_status()

                response = response.json()

                try:
                    edge_media_to_parent_comment = response["data"][
                        "shortcode_media"
                    ]["edge_media_to_parent_comment"]

                    return edge_media_to_parent_comment

                except KeyError:

                    return []

                for edge in edge_media_to_parent_comment["edges"]:

                    comment_node = edge["node"]

                    comment = PostComment(comment_node)

                    counter = +counter

                    yield comment

                next_page = edge_media_to_parent_comment["page_info"][
                    "has_next_page"
                ]

                end_cursor = edge_media_to_parent_comment["page_info"][
                    "end_cursor"
                ]

            except (
                requests.exceptions.Timeout,
                requests.exceptions.HTTPError,
                requests.exceptions.ConnectionError,
                requests.exceptions.ChunkedEncodingError,
                json.JSONDecodeError,
            ) as e:
                logger.error(
                    "Error mientras se hace el requests de comentarios",
                    error=e,
                )

                if retry > 0:
                    logger.info(
                        "Re intentando sacar comentarios, actualmente:",
                        cantidad_comentarios=counter,
                    )
                    yield from self.scrape_post_comments(
                        post_id=post_id,
                        n_comments=n_comments,
                        end_cursor=end_cursor,
                        retry=retry - 1,
                        timeout=timeout,
                    )

                return []
