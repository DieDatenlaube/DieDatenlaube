#!/usr/bin/env python
# coding: utf-8
"""run.py - Orchestrierung des Gartenlaube-Artikel-Parsers.

Abgleich der Artikel zwischen de.wikisource und Wikidata im Rahmen des
de.wikisource-Projekts zum Album der sächsischen Industrie.

Workflow (aus dem Notebook ParseWikiSource_ByCategories__GartenlaubeArtikelParser.ipynb):
1. Hauptkategorie "Kategorie:Die_Gartenlaube_Artikel" auf de.wikisource abrufen
2. Alle Unterkategorien (Jahrgänge) ermitteln
3. Pro Unterkategorie alle Seiten (Artikel) paginiert abrufen
4. Pro Seite prüfen, ob ein Wikidata-Item existiert (SPARQL-Massenabfrage,
   Fallback MediaWiki-API)
5. Bei fehlendem Wikidata-Item: Seite laden, Vorlage {{Textdaten}} auslesen
   und Metadaten für den Wikidata-Import sammeln (resultSet)
6. QuickStatements-TSV für den Import schreiben

Ausgaben (JSON-Ergebnis, existierende QIDs, QS-TSV, Logdatei) landen
im Verzeichnis output/. Alle Konsolenausgaben des Notebooks werden über
logging in eine Logdatei geschrieben.
"""

import json
import os
import sys
import time
import urllib.parse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.logging_setup import setup_logging
from src.quickstatements import write_quickstatements
from src.sparql_query import build_title_qid_map, fetch_all_gartenlaube_articles
from src.textdaten import parse_textdaten
from src.wikisource_api import MediaWikiAPI

WIKISOURCE_API_URL = "https://de.wikisource.org/w/api.php"
USER_AGENT = (
    "GartenlaubeParser/1.0 "
    "(https://de.wikisource.org/wiki/Wikisource:WikiProjekt_Illustrierte_Zeitschriften; "
    "contact via wikisource)"
)
ROOT_CATEGORY = "Kategorie:Die_Gartenlaube_Artikel"
CHECKPOINT_INTERVAL = 100  # Zwischenspeichern des resultSet alle 100 Artikel


class GartenlaubeArtikelParser:
    """Workflow: Kategorie -> Unterkategorien -> Seiten -> Textdaten -> resultSet."""

    def __init__(self, api, title_qid_map, base_output_file, exist_qid_file, qs_file, logger):
        self.api = api
        self.title_qid_map = title_qid_map
        self.base_output_file = base_output_file
        self.exist_qid_file = exist_qid_file
        self.qs_file = qs_file
        self.logger = logger
        self.artikel_counter = 1
        self.result_set = []

    def process_article(self, artikel):
        """Verarbeitet einen einzelnen Kategorie-Eintrag (Artikel-Seite)."""
        wikisource_titel = (
            artikel["title"] + " https://de.wikisource.org/?curid=" + str(artikel["pageid"])
        )
        result_det = {}

        # Get Wikidata QID: zuerst in der SPARQL-Massenabfrage, sonst MW-API
        wdid = self.title_qid_map.get(artikel["title"])
        if wdid is None:
            wdid = self.api.wikibase_item(artikel["title"])
        self.logger.info("%s", wdid)

        if wdid is None:
            self.logger.info(
                "#%s we need a wikidata item for %s", self.artikel_counter, wikisource_titel
            )
            textdata = self.api.page_wikitext(artikel["title"])
            if textdata is None:
                return
            result_det["Sdewikisource"] = artikel["title"]

            oldid = self.api.lastrevid(artikel["title"])
            perm_link = (
                "https://de.wikisource.org/w/index.php?title="
                + urllib.parse.quote_plus(artikel["title"])
                + "&oldid=" + str(oldid)
            )
            self.logger.info(perm_link)
            result_det["permLink"] = perm_link

            for page in textdata["query"]["pages"]:
                wikitext = textdata["query"]["pages"][page]["revisions"][0]["*"]
                result_det.update(parse_textdaten(wikitext, self.api, self.logger))

            if "titel" in result_det:
                self.result_set.append(dict(result_det))

            write_quickstatements([result_det], self.qs_file, self.logger)
        else:
            self.logger.info(
                "#%s %s already exists for %s", self.artikel_counter, wdid, wikisource_titel
            )
            # Hier könnten die vorhandenen QIDs gesammelt und für eine SPARQL-Query
            # mit großem VALUE [] genutzt werden, um die Datenqualität der vorhandenen
            # Einträge zu überprüfen
            with open(self.exist_qid_file, "a", encoding="utf-8") as fa:
                fa.write(str(wdid) + "\n")

        self.artikel_counter += 1
        self.logger.info("--------------------------------------------------------------------------")

    def checkpoint(self):
        """Zwischenspeichern des resultSet als JSON (alle CHECKPOINT_INTERVAL Artikel)."""
        with open(self.base_output_file, "w", encoding="utf-8") as f:
            json.dump(self.result_set, f)
        self.logger.info("Checkpoint saved at article %s", self.artikel_counter)

    def runthrough_cat(self, cmtitle):
        """Alle Seiten einer (Unter-)Kategorie paginiert durchlaufen."""
        for artikel in self.api.iter_category_members(cmtitle):
            self.process_article(artikel)
            if self.artikel_counter % CHECKPOINT_INTERVAL == 0:
                self.checkpoint()

    def runthrough_subcat(self, kategorie):
        """Alle Unterkategorien der Hauptkategorie durchlaufen."""
        for subcat in self.api.list_subcategories(kategorie):
            self.logger.info(">>=============================================")
            self.logger.info(subcat)
            self.runthrough_cat(subcat)

    def write_result_set(self):
        """Endergebnis: baseOutputFile neu schreiben und resultSet als JSON anhängen."""
        try:
            os.remove(self.base_output_file)
        except OSError:
            pass
        with open(self.base_output_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(self.result_set))


def main():
    timestamp = str(time.time())[0:10]
    output_dir = os.path.join(BASE_DIR, "output")
    os.makedirs(output_dir, exist_ok=True)

    base_output_file = os.path.join(output_dir, "gartenlaube" + timestamp + ".json")
    exist_qid_file = os.path.join(output_dir, "existQID" + timestamp + ".txt")
    qs_file = os.path.join(output_dir, "qs" + timestamp + ".tsv")
    log_file = os.path.join(output_dir, "gartenlaube_parser_" + timestamp + ".log")
    for path in (exist_qid_file, qs_file):
        try:
            os.remove(path)
        except OSError:
            pass

    logger = setup_logging(log_file)
    logger.info("Logdatei: %s", log_file)
    logger.info("Starte Parser für %s auf de.wikisource", ROOT_CATEGORY)

    api = MediaWikiAPI(WIKISOURCE_API_URL, USER_AGENT, logger)

    # Alle vorhandenen Gartenlaube-Artikel in Wikidata per SPARQL laden
    all_gartenlaube_artikel = fetch_all_gartenlaube_articles(logger=logger)
    title_qid_map = build_title_qid_map(all_gartenlaube_artikel)
    logger.info("%s vorhandene Gartenlaube-Artikel in Wikidata gefunden", len(title_qid_map))

    parser = GartenlaubeArtikelParser(
        api, title_qid_map, base_output_file, exist_qid_file, qs_file, logger
    )
    parser.runthrough_subcat(ROOT_CATEGORY)
    parser.write_result_set()

    logger.info(
        "Fertig: %s Artikel ohne Wikidata-Item in %s, QS-Import in %s",
        len(parser.result_set), base_output_file, qs_file,
    )


if __name__ == "__main__":
    main()
