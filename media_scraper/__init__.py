# -*- coding: utf-8 -*-
"""Inicialización del paquete."""

from media_scraper._logging import configure_logging
from media_scraper.settings import init_project_settings

SETTINGS = init_project_settings()


logger = configure_logging(
    "media_scraper", SETTINGS, kidnap_loggers=True
)


def get_connection():

    from elastinga.connection import ElasticSearchConnection

    return ElasticSearchConnection().connection


ELASTIC_CONNECTION = get_connection()
"""Conexión a elasticsearch. Notar que no es una conexión activa"""
