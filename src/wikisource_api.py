#!/usr/bin/env python
# coding: utf-8
"""Zugriff auf die MediaWiki-API von de.wikisource (CategoryMembers & Co.).

Kapselt alle API-Aufrufe des Notebooks:
* Kategorie-Mitglieder (Seiten und Unterkategorien) inkl. cmcontinue-Paginierung
* wikibase_item (QID) einer Seite via pageprops
* lastrevid einer Seite via prop=info
* Wikitext einer Seite via prop=revisions
"""

import json
import logging
import time

import requests


def safe_json(response, retries=3, logger=None):
    """Sicheres JSON-Parsing mit Retry bei Rate-Limiting (429) oder leeren Antworten."""
    log = logger or logging.getLogger(__name__)
    for i in range(retries):
        try:
            if response.status_code == 429:
                wait = 2 ** i
                log.warning("Rate limited (429), waiting %ss...", wait)
                time.sleep(wait)
                continue
            response.raise_for_status()
            if not response.text.strip():
                raise ValueError("Empty response body")
            return response.json()
        except (json.JSONDecodeError, ValueError, requests.exceptions.RequestException):
            if i == retries - 1:
                log.error(
                    "JSON parse failed after %s retries. Status: %s, Body: %s",
                    retries, response.status_code, response.text[:200],
                )
                return None
            time.sleep(1)
    return None


class MediaWikiAPI:
    """Klient für die MediaWiki-API eines Wikis (Default: de.wikisource)."""

    def __init__(self, url, user_agent, logger=None, pause=0.1):
        self.url = url
        self.pause = pause
        self.logger = logger or logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

    def get_json(self, params, url=None):
        """Generischer GET-Aufruf auf die API mit JSON-Antwort (None bei Fehler)."""
        time.sleep(self.pause)
        response = self.session.get(url=url or self.url, params=params)
        return safe_json(response, logger=self.logger)

    def iter_category_members(self, cmtitle, cmtype=None, cmlimit=500):
        """Liefert alle Mitglieder einer Kategorie, paginiert über cmcontinue.

        :param cmtitle: Kategorietitel, z. B. "Kategorie:Die_Gartenlaube_Artikel"
        :param cmtype: None für Seiten, "subcat" für Unterkategorien
        """
        # frische Parameter pro Kategorie, damit kein veralteter
        # cmcontinue in die nächste Kategorie übernommen wird
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": cmtitle,
            "cmlimit": cmlimit,
            "format": "json",
        }
        if cmtype is not None:
            params["cmtype"] = cmtype
        while True:
            data = self.get_json(params)
            if data is None or "query" not in data:
                self.logger.warning(
                    "Warning: Received None/empty from API for %s, skipping category", cmtitle
                )
                return
            try:
                members = data["query"]["categorymembers"]
            except KeyError:
                return
            yield from members
            if "continue" in data and "cmcontinue" in data["continue"]:
                params["cmcontinue"] = data["continue"]["cmcontinue"]
            else:
                return

    def list_subcategories(self, cmtitle):
        """Liste aller Unterkategorien einer Kategorie (paginiert)."""
        return [m["title"] for m in self.iter_category_members(cmtitle, cmtype="subcat")]

    def wikibase_item(self, pagetitle, url=None):
        """QID (wikibase_item) einer Seite, oder None wenn kein Wikidata-Item verknüpft ist."""
        params = {
            "action": "query",
            "prop": "pageprops",
            "ppprop": "wikibase_item",
            "redirects": 1,
            "titles": pagetitle,
            "format": "json",
        }
        data = self.get_json(params, url=url)
        if data is None:
            return None
        try:
            for page in data["query"]["pages"]:
                try:
                    return data["query"]["pages"][page]["pageprops"]["wikibase_item"]
                except KeyError:
                    pass
        except KeyError:
            pass
        return None

    def lastrevid(self, pagetitle):
        """lastrevid (alte ID) einer Seite für den Permalink."""
        params = {
            "action": "query",
            "prop": "info",
            "redirects": 1,
            "titles": pagetitle,
            "format": "json",
        }
        data = self.get_json(params)
        if data is None:
            return None
        for page in data["query"]["pages"]:
            try:
                return data["query"]["pages"][page]["lastrevid"]
            except KeyError:
                pass
        return None

    def page_wikitext(self, pagetitle):
        """Aktuellen Wikitext einer Seite (prop=revisions, rvprop=content)."""
        params = {
            "action": "query",
            "prop": "revisions",
            "rvprop": "content",
            "rvlimit": 1,
            "titles": pagetitle,
            "format": "json",
        }
        return self.get_json(params)
