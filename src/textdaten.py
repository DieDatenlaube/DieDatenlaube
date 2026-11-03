#!/usr/bin/env python
# coding: utf-8
"""Auslesen der Vorlage {{Textdaten}} aus dem Wikitext einer de.wikisource-Seite.

Extrahiert die Metadatenfelder per Regex und baut daraus das Ergebnis-Dict
für den Wikidata-Import (resultSet-Eintrag).
"""

import logging
import re

DE_WIKIPEDIA_API_URL = "https://de.wikipedia.org/w/api.php"
GARTENLAUBE_QID = "Q655617"


def parse_textdaten(wikitext, api, logger=None):
    """Parst die {{Textdaten}}-Felder aus dem Wikitext einer Artikelseite.

    :param wikitext: Roh-Wikitext der Seite (prop=revisions, rvprop=content)
    :param api: MediaWikiAPI-Instanz für QID-Nachschläge (Autor, Schlagwort)
    :param logger: Logger für die Ausgaben
    :return: Dict mit den extrahierten Metadaten (resultSet-Eintrag)
    """
    log = logger or logging.getLogger(__name__)
    result = {}

    # TITEL (plain oder [[Link|Anzeige]] bzw. [[Link]])
    regex = r"\|TITEL=((\[\[((.*(?<=\|)(.*?))|(.*?))\]\])|(.*))"
    matches = re.finditer(regex, wikitext, re.MULTILINE)
    for matchNum, match in enumerate(matches, start=1):
        if match.group(5) != None:
            log.info(match.group(5))
            result["titel"] = match.group(5).strip()
        elif match.group(7) != None:
            log.info(match.group(7))
            result["titel"] = match.group(7).strip()
        else:
            log.info(match.group(3))
            result["titel"] = match.group(3).strip()

    regex = r"\|SUBTITEL=(.*)"
    matches = re.finditer(regex, wikitext, re.MULTILINE)
    for matchNum, match in enumerate(matches, start=1):
        log.info("Untertitel: " + match.group(1))
        result["untertitel"] = match.group(1)

    regex = r"\|JAHR=(.*)"
    matches = re.finditer(regex, wikitext, re.MULTILINE)
    for matchNum, match in enumerate(matches, start=1):
        log.info("Erscheinungsjahr: " + match.group(1))
        erscheinungsjahr = match.group(1)
        result["erscheinungsjahr"] = erscheinungsjahr

    regex = r"\|Seite=(.*)"
    matches = re.finditer(regex, wikitext, re.MULTILINE)
    for matchNum, match in enumerate(matches, start=1):
        log.info("Seite: " + match.group(1))
        seite = match.group(1)
        if seite != "":
            result["seite"] = seite.strip()

    regex = r"\|Heft=(.*)"
    matches = re.finditer(regex, wikitext, re.MULTILINE)
    for matchNum, match in enumerate(matches, start=1):
        log.info("Heft: " + match.group(1))
        heft = match.group(1)
        # Link-Schreibweise [[Ziel|Anzeige]] auf die Anzeige reduzieren
        heft = re.sub(r"\[\[(.*)\|(.*)\]\]", r"\2", heft)
        result["heft"] = heft

    regex = r"\|AUTOR=(.*)"
    regexAut = r"\[\[((.*(?<=\|)(.*?))|(.*?))\]]"
    matches = re.finditer(regex, wikitext, re.MULTILINE)
    for matchNum, match in enumerate(matches, start=1):
        log.info("Autor Gesamt: " + match.group(1))
        autor = match.group(1).strip()
        matches = re.finditer(regexAut, autor, re.MULTILINE)
        autorLis = []
        autorQIDLis = []
        autorStr = []
        for matchNumAut, matchAut in enumerate(matches, start=1):
            if matchAut.group(3) != None:
                log.info("Autor: " + matchAut.group(3))
                autorLis.append(matchAut.group(3))
                autorStr.append(matchAut.group(3).strip())
            else:
                log.info("Autor: " + matchAut.group(1))
                autorLis.append(matchAut.group(1))
                autorStr.append(matchAut.group(1).strip())
            autorqid = api.wikibase_item(matchAut.group(1))
            log.info("autorQID: %s", autorqid)
            autorQIDLis.append(autorqid)

        result["autor"] = autorLis
        log.info(result["autor"])
        result["autorQID"] = autorQIDLis
        log.info(result["autorQID"])
        if len(autorStr) == 0:
            result["autorStr"] = [autor]
        else:
            result["autorStr"] = autorStr

    regex = r"\|WIKIPEDIA=(.*)"
    matches = re.finditer(regex, wikitext, re.MULTILINE)
    for matchNum, match in enumerate(matches, start=1):
        log.info("Main Subject: " + match.group(1))
        mainsub = match.group(1)
        result["mainSubject"] = mainsub
        msQID = api.wikibase_item(mainsub, url=DE_WIKIPEDIA_API_URL)
        result["mainSubjectQID"] = msQID
        log.info("mainSubQID: %s", msQID)

    # Fixe Parameter
    result["gartenlaube"] = GARTENLAUBE_QID
    log.info(result["gartenlaube"])
    try:
        deDesc = "Artikel in: Die Gartenlaube, " + erscheinungsjahr + ", Heft " + heft
        result["deDesc"] = deDesc
        log.info(deDesc)

        enDesc = "german article in Die Gartenlaube" + ", " + erscheinungsjahr + ", no. " + heft
        result["enDesc"] = enDesc
        log.info(enDesc)

        nlDesc = "redactioneel artikel in Die Gartenlaube (" +erscheinungsjahr+"), nr. " + heft
        result["nlDesc"] = nlDesc
        log.info(nlDesc)

        hsbDesc = "němski nastawk w: Die Gartenlaube (" + erscheinungsjahr + "), čo. " + heft
        result["hsbDesc"] = hsbDesc
        dsbDesc = "nimski nastawk w: Die Gartenlaube (" + erscheinungsjahr + "), c. " + heft
        result["dsbDesc"] = dsbDesc
    except NameError:
        # JAHR oder Heft fehlt in der Vorlage -> keine Beschreibungen
        pass

    return result
