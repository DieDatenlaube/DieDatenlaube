#!/usr/bin/env python
# coding: utf-8
"""SPARQL-Abfragen gegen den Wikidata-Endpunkt (QLever statt WDQS, weniger Rate-Limiting).

Enthält:
* get_results: generische SPARQL-Ausführung mit Retry bei 429
* get_wikibase_id_via_sparql: QID eines einzelnen Artikels per SPARQL
* fetch_all_gartenlaube_articles: Massenabfrage aller Gartenlaube-Artikel mit QID
* build_title_qid_map: Mapping Seitentitel -> QID aus dem Massenabfrage-Ergebnis
"""

import logging
import re
import sys
import time

from SPARQLWrapper import SPARQLWrapper, JSON

ENDPOINT_URL = "https://qlever.dev/api/wikidata"  # QLever statt WDQS (weniger Rate-Limiting)

# Massenabfrage: alle Wikidata-Items, die als "erschienen in Die Gartenlaube" (P1433 Q655617)
# mit einer de.wikisource-Seite verknüpft sind
GARTENLAUBE_ARTIKEL_QUERY = """PREFIX schema: <http://schema.org/>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
SELECT * WHERE {
  ?gartenlaubeArtikel wdt:P1433 wd:Q655617.
  ?wsPage schema:about ?gartenlaubeArtikel;
    schema:isPartOf <https://de.wikisource.org/>.
  ?wsPage schema:name ?wsPageName
}"""

# SPARQL-Abfrage der QID eines einzelnen Artikels anhand seines Seitentitels
ARTIKEL_VIA_TITEL_QUERY_TEMPLATE = """PREFIX schema: <http://schema.org/>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
SELECT * WHERE {
  ?gartenlaubeArtikel wdt:P1433 wd:Q655617.
  ?article schema:about ?gartenlaubeArtikel.
  ?article schema:isPartOf <https://de.wikisource.org/>.
  ?article schema:name ?pageTitle.
  FILTER(STR(?pageTitle)='%s')
}"""


def get_results(endpoint_url, query, max_retries=5, logger=None):
    """Führt eine SPARQL-Query aus, mit Retry bei Rate-Limiting (429)."""
    log = logger or logging.getLogger(__name__)
    user_agent = (
        "GartenlaubeParser/1.0 "
        "(https://de.wikisource.org/wiki/Wikisource:WikiProjekt_Illustrierte_Zeitschriften; "
        "Python/%s.%s)" % (sys.version_info[0], sys.version_info[1])
    )
    for attempt in range(max_retries):
        try:
            sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            # QLever ist schneller, kein langer Sleep nötig
            return sparql.query().convert()
        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                wait = 10 * (attempt + 1)
                log.warning(
                    "SPARQL rate-limited (429), waiting %ss before retry %s/%s...",
                    wait, attempt + 1, max_retries,
                )
                time.sleep(wait)
            else:
                log.warning("SPARQL error (non-429): %s", e)
                if attempt == max_retries - 1:
                    raise
                time.sleep(5)
    raise RuntimeError("SPARQL failed after %s retries" % max_retries)


def get_wikibase_id_via_sparql(pagetitle, endpoint_url=ENDPOINT_URL, logger=None):
    """QID eines einzelnen Artikels per SPARQL anhand des Seitentitels."""
    query = ARTIKEL_VIA_TITEL_QUERY_TEMPLATE % str(pagetitle)
    return get_results(endpoint_url, query, logger=logger)


def fetch_all_gartenlaube_articles(endpoint_url=ENDPOINT_URL, logger=None):
    """Massenabfrage aller Gartenlaube-Artikel mit QID.

    Bei Fehlschlag Fallback auf eine leere Ergebnismenge, dann werden
    die QIDs einzeln pro Artikel über die MediaWiki-API nachgeschlagen.
    """
    log = logger or logging.getLogger(__name__)
    try:
        return get_results(endpoint_url, GARTENLAUBE_ARTIKEL_QUERY, logger=log)
    except Exception as e:
        log.warning(
            "SPARQL initial query failed, falling back to per-article MW API lookups: %s", e
        )
        return {"results": {"bindings": []}}


def build_title_qid_map(sparql_result):
    """Baut aus dem SPARQL-Ergebnis ein Dict {wikisource-Seitentitel: QID}."""
    mapping = {}
    for result in sparql_result["results"]["bindings"]:
        qid = re.sub(
            r"http://www\.wikidata\.org/entity/", "", result["gartenlaubeArtikel"]["value"]
        )
        mapping[result["wsPageName"]["value"]] = qid
    return mapping
