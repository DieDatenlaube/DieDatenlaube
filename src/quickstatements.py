#!/usr/bin/env python
# coding: utf-8
"""Aufbau der QuickStatements-TSV für den Wikidata-Import.

String-Konkatenation der QuickStatements-Befehle (CREATE/LAST ...) aus einem
Ergebnis-Dict (resultSet-Eintrag) und Anhängen an die QS-Datei.
"""

import logging
import re


def write_quickstatements(results, qs_file, logger=None):
    """Schreibt für jedes Ergebnis-Dict einen QuickStatements-Block an die QS-Datei an.

    :param results: Liste von resultSet-Einträgen (Dicts aus parse_textdaten)
    :param qs_file: Pfad zur QS-TSV-Datei (wird im Append-Modus geöffnet)
    :param logger: Logger für Debug-Ausgaben
    """
    log = logger or logging.getLogger(__name__)
    log.debug(results)
    with open(qs_file, "a", encoding="utf-8") as f:
        for result in results:
            try:
                reference = '\tS143\tQ15522295\tS4656\t"' + result["permLink"] + '"'
            except KeyError:
                reference = ""

            print("CREATE", file=f)
            # Labels, Descriptions
            print('LAST\tSdewikisource\t"' + result["Sdewikisource"] + '"', file=f)
            print('LAST\tLde\t"' + result["titel"] + '"', file=f)
            print('LAST\tLen\t"' + result["titel"] + '"', file=f)
            print('LAST\tLnl\t"' + result["titel"] + '"', file=f)

            try:
                print('LAST\tDen\t"' + result["enDesc"] + '"', file=f)
            except KeyError:
                pass
            try:
                print('LAST\tDde\t"' + result["deDesc"] + '"', file=f)
            except KeyError:
                pass
            try:
                print('LAST\tDnl\t"' + result["nlDesc"] + '"', file=f)
            except KeyError:
                pass
            try:
                print('LAST\tDhsb\t"' + result["hsbDesc"] + '"', file=f)
            except KeyError:
                pass
            try:
                print('LAST\tDdsb\t"' + result["dsbDesc"] + '"', file=f)
            except KeyError:
                pass

            # Instance of Article
            print("LAST\tP31\tQ191067", file=f)

            if len(result["autorQID"]) > 0:
                try:
                    for autcunt, autoren in enumerate(result["autorQID"]):
                        try:
                            print(
                                "LAST\tP50\t" + autoren
                                + '\tP1932\t"' + result["autor"][autcunt] + '"'
                                + '\tP1545\t"' + str(autcunt + 1) + '"' + reference,
                                file=f,
                            )
                        except TypeError:
                            for autorenStr in result["autorStr"]:
                                if autorenStr == "unbekannt":
                                    print("LAST\tP2093\tsomevalue" + reference, file=f)
                                elif autorenStr != "":
                                    print('LAST\tP2093\t"' + autorenStr + '"' + reference, file=f)
                except KeyError:
                    try:
                        for autorenStr in result["autorStr"]:
                            if autorenStr == "unbekannt":
                                print("LAST\tP2093\tsomevalue" + reference, file=f)
                            elif autorenStr != "":
                                print('LAST\tP2093\t"' + autorenStr + '"' + reference, file=f)
                    except KeyError:
                        pass
            else:
                try:
                    for autorenStr in result["autorStr"]:
                        if autorenStr == "unbekannt":
                            print("LAST\tP2093\tsomevalue" + reference, file=f)
                        elif autorenStr != "":
                            print('LAST\tP2093\t"' + autorenStr + '"' + reference, file=f)
                except KeyError:
                    pass

            print('LAST\tP1476\tde:"' + result["titel"] + '"' + reference, file=f)
            if re.search("^Briefkasten", result["titel"]):
                print("LAST\tP31\tQ651270" + reference, file=f)
            if re.search("^Berichtigung", result["titel"]):
                print("LAST\tP31\tQ1348305" + reference, file=f)

            try:
                if result["untertitel"] != "":
                    print('LAST\tP1680\tde:"' + result["untertitel"] + '"' + reference, file=f)
            except KeyError:
                pass
            print("LAST\tP407\tQ188", file=f)
            print(
                "LAST\tP577\t+" + result["erscheinungsjahr"].strip() + "-00-00T00:00:00Z/9" + reference,
                file=f,
            )
            try:
                print('LAST\tP304\t"' + result["seite"] + '"' + reference, file=f)
                seiteasQual = '\tP304\t"' + result["seite"] + '"'
            except KeyError:
                seiteasQual = ""
            try:
                print('LAST\tP433\t"' + result["heft"] + '"' + reference, file=f)
                heftasQual = '\tP433\t"' + result["heft"] + '"'
            except KeyError:
                heftasQual = ""

            print(
                "LAST\tP1433\t" + result["gartenlaube"]
                + seiteasQual
                + heftasQual
                + "\tP577\t+" + result["erscheinungsjahr"].strip() + "-00-00T00:00:00Z/9" + reference,
                file=f,
            )
            try:
                print("LAST\tP921\t" + result["mainSubjectQID"] + reference, file=f)
            except (KeyError, TypeError):
                pass
