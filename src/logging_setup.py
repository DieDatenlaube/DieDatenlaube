#!/usr/bin/env python
# coding: utf-8
"""Logging-Setup für den Gartenlaube-Artikel-Parser.

Ersetzt die print-Ausgaben des Notebooks: alle Ausgaben gehen
in eine Logdatei (und parallel auf die Konsole).
"""

import logging

LOGGER_NAME = "gartenlaube_parser"


def setup_logging(logfile):
    """Konfiguriert den Logger 'gartenlaube_parser' mit File- und Stream-Handler.

    :param logfile: Pfad zur Logdatei
    :return: der konfigurierte Logger
    """
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    if logger.handlers:
        # bereits konfiguriert (z. B. bei erneutem Aufruf)
        return logger
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    file_handler = logging.FileHandler(logfile, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger
