# -*- coding: utf-8 -*-
"""Utilidades comunes para los scrapers."""

from itertools import cycle

import requests
from bs4 import BeautifulSoup

PROXY_URL = "https://free-proxy-list.net/"


class ProxiesRequests:
    """"Clase que provee generador de proxys cíclico."""

    def __init__(self):
        self._requests = requests.Session()
        self.proxies_pool = cycle(self.get_proxies())

    def get_proxies(self):
        """Parser para obtener proxies públicos."""
        response = requests.get(PROXY_URL)
        soup = BeautifulSoup(response.text, "lxml")
        table = soup.find("table", id="proxylisttable")
        list_tr = table.find_all("tr")
        list_td = [elem.find_all("td") for elem in list_tr]
        list_td = list(filter(None, list_td))
        list_ip = [elem[0].text for elem in list_td]
        list_ports = [elem[1].text for elem in list_td]
        list_proxies = [
            ":".join(elem) for elem in list(zip(list_ip, list_ports))
        ]
        return list_proxies
