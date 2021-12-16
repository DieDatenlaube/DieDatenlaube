#!/usr/bin/env python
# coding: utf-8

# # Get all the Gartenlaube Text in Wikisource
# 
# Mehr als 15.000 Artikel der Gartenlaube sind Ende 2021 in Wikisource erschlossen, ein vielfaches an Seiten der Illustrierten stehen hinter diesen Artikeln. 
# 
# ## Frage 
# 
# Wie kommt man zum Texttranskript aller Gartenlaube-Artikel in Wikisource? (vgl. https://de.wikisource.org/wiki/Benutzer_Diskussion:Jeb#Gartenlaube_runterladen)
# 
# ## Let's hack
# 
# Die MediaWiki-API bietet eine Vielzahl an Methoden um Daten aus MediaWikis - wie Wikisource - maschinell und im großen Stil zu extrahieren. Für große Projekte wie die Gartenlaube, die letztlich auch so sturkturiert sind wie sie strukturiert sind, geht es aber nicht ganz ohne Code. 
# 
# Was muss vorab beachtet werden?
# 
# * Der Text von Wikisource-Artikeln liegt nicht in den Seiten der strukturierten Zeitschriftenartikel, sondern in den Wiki-Artikel des `Seite:`-Namespaces
# * Ein Wikisource-Großprojekt wie Die Gartenlaube ist nicht in einer einzigen Projektkategorie organisiert. Die einzelnen Seiten liegen in Jahrgangskategorien vor, die selbst eine Unterkategorie der Gartenlaube-Kategorie sind.
# * Die MediaWiki-API bietet eine Extension an, um möglichst "Plain"-Text zu erhalten. Diese Extension `TextExctracts`(https://www.mediawiki.org/wiki/Extension:TextExtracts/de) ist aber für die Wikisource nicht verfügbar, da hier die Extension Proofread dies technisch gegenwärtig nicht ermöglicht. Daher ist ein Text-Output nur in einem gerenderte HTML oder im Wikitext möglich. Beide Varianten werden am Ende dieses Skripts im Output vereint.
# * Mit der Python-Library `mwparserfromhell` wird noch zusätzlich ein plaintext ausgegeben, dieser Text basiert auf dem Wikicode, verliert aber sämtliche Textinhalte, die in Vorlagen gespeichert waren. Konkret sind dies Überschriften und Bildunterschriften. Dieser Volltext ist daher nur als Referenzwert zu verstehen und mit Vorsicht zu genießen.
# 
# ### 1. Schritt - Alle Jahrgangskategorien parsen

# In[4]:


import requests

S = requests.Session()

URL = "https://de.wikisource.org/w/api.php"

PARAMS = {
    "action": "query",
    "cmtitle": "Kategorie:Die Gartenlaube",
    "cmlimit":500,
    "cmtype": "subcat",
    "list": "categorymembers",
    "format": "json"
}

R = S.get(url=URL, params=PARAMS)
DATA = R.json()

Gartenlaube_SubCat = DATA["query"]["categorymembers"]

#for SubCat in Gartenlaube_SubCat:
#    print(SubCat["title"])


# ### 2. Für jede Subkategorie der Gartenlaube, Seiten des "Seite:"-Namespaces abrufen

# In[5]:


pages = []
retDict = {}
for SubCat in Gartenlaube_SubCat:
    catPages = []
    PARAMS = {
    "action": "query",
    "gcmtitle": SubCat["title"],
    "gcmlimit": 500,
    "gcmnamespace":102,
    "generator": "categorymembers",
    "prop": "proofread|info",
    "format": "json"
    }

    R = S.get(url=URL, params=PARAMS)
    DATA = R.json()
    
    try:
        Gartenlaube_Seiten = DATA["query"]["pages"]
        #print(DATA)

        for Pages in Gartenlaube_Seiten:
            print(Gartenlaube_Seiten[Pages])
            pagedet = {}
            pagedet["pageid"] = Gartenlaube_Seiten[Pages]["pageid"]
            pagedet["title"] = Gartenlaube_Seiten[Pages]["title"]
            pagedet["proofread"] = Gartenlaube_Seiten[Pages]["proofread"]
            pagedet["lastrevid"] = Gartenlaube_Seiten[Pages]["lastrevid"]
            catPages.append(pagedet)

        try:
            PARAMS["gcmcontinue"] = DATA["continue"]["gcmcontinue"]
            R = S.get(url=URL, params=PARAMS)
            DATA = R.json()
            Gartenlaube_Seiten = DATA["query"]["pages"]
            for Pages in Gartenlaube_Seiten:
                pagedet = {}
                pagedet["pageid"] = Gartenlaube_Seiten[Pages]["pageid"]
                pagedet["title"] = Gartenlaube_Seiten[Pages]["title"]
                pagedet["proofread"] = Gartenlaube_Seiten[Pages]["proofread"]
                pagedet["lastrevid"] = Gartenlaube_Seiten[Pages]["lastrevid"]
                catPages.append(pagedet)
                #print(Pages["title"])
        except KeyError:
            pass

        
    except KeyError:
        pass
    
    retDict[SubCat["title"]]=catPages
pages.append(retDict)
#print(pages)


# ### 3. Für jede Seite die zugehörigen Text auslesen
# 
# * Für jeden Jahrgang wird ein JSON-File erzeugt nach dem Muster `GartenlaubeSeitenText_{Jahrgangskategorie}_{Timestamp}.json`und beinhaltet ein JSON-Objekt mit folgender Struktur:
# ```json
#  [{"pageid" : {PAGEID},
#    "title"   : {PAGETITLE},
#    "html"    : {HTML_OUTPUT},
#    "wikitext": {WIKI_MARKUP},
#    "plaintxt": {mwparserfromhell(WIKI_MARKUP).strip_code)}
#    }]
#  ```

# In[6]:

import mwparserfromhell
import time
import json

#print(pages[0]["Kategorie:Die Gartenlaube (1853)"])
#https://de.wikisource.org/w/api.php?action=parse&format=json&pageid=197745&prop=text%7Cwikitext

for page in pages[0]:
    SeitenText = []
    for wikisourcePage in pages[0][page]:
        print(wikisourcePage)
    
        PARAMS = {
        "action": "parse",
        "pageid": wikisourcePage["pageid"],
        "pageid": 197745,
        "prop":"text|wikitext",
        "format": "json"
        }
        R = S.get(url=URL, params=PARAMS)
        DATA = R.json()
        SeitenTextDet = {}
        SeitenTextDet["pageid"] = wikisourcePage["pageid"]
        SeitenTextDet["title"] = wikisourcePage["title"]
        SeitenTextDet["proofread"] = wikisourcePage["proofread"]
        SeitenTextDet["lastrevid"] = wikisourcePage["lastrevid"]
        SeitenTextDet["html"] = DATA["parse"]["text"]["*"]
        SeitenTextDet["wikitext"] = DATA["parse"]["wikitext"]["*"]
        wikicode = mwparserfromhell.parse(SeitenTextDet["wikitext"] )
        SeitenTextDet["plaintxt"] = wikicode.strip_code()
        SeitenText.append(SeitenTextDet)

    f = open("output/GartenlaubeSeitenText_"+page+"_"+str(time.time())[0:10]+".json", "w")
    print(json.dumps(SeitenText),file=f)
    f.close()      


# ### 4. Merge der Jahrgangs-Files
# 
# * Die bestehenden Jahrgangs-Jsonfiles werden hier zu einer Gesamtdatei gemerged. 
# * **Achtung**: Dieser Schritt läuft nur als python-Skript via Shell, nicht im Notebook.

# In[ ]:


import glob
import time

read_files = glob.glob("/home/librerli/wikinotebooks/gartenlaube/DieDatenlaube/output/*.json")
print(read_files)

with open("/home/librerli/wikinotebooks/gartenlaube/DieDatenlaube/output/GartenlaubeSeiten_Text_"+str(time.time())[0:10]+".json", "wb") as outfile:
    outfile.write(b",".join([open(f, "rb").read() for f in read_files]))

