# Die Datenlaube

This repository containing scripts, documentation and data around the project [#DieDatenlaube](https://twitter.com/search?q=%23DieDatenlaube&src=typed_query) - increasing visibality and discoverability of articles of Die Gartenlaube in Wikidata

## Blog
* [Die Datenlaube Blog](https://diedatenlaube.github.io)

## Jupyter Notebooks
* [ParseWikiSource_ByCategories__GartenlaubeArtikelParser.ipynb](Notebooks/ParseWikiSource_ByCategories__GartenlaubeArtikelParser.ipynb) - **Original** & **Datenlaube-Core** Jupyter Notebook to parse Wikicategory "Die Gartenlaube" and extract the Wiki-Infotemplate on German Wikisource and creating a QuickStatements-Import
* [Get_Gartenlaube_SeitenText.ipynb](Notebooks/Get_Gartenlaube_SeitenText.ipynb) - Jupyter Notebook to get the full text transcriptions of all Die Gartenlaube articles in Wikisource
* [ExtractGartenlaubeImages_byCategories.ipynb](Notebooks/ExtractGartenlaubeImages_byCategories.ipynb) - Extrahiert freigestellte Illustrationen der Gartenlaube aus den Wikisource-Artikeln
* [Split_Pages_Articles.ipynb](Notebooks/Split_Pages_Articles.ipynb) - Bereinigt Seiten- und Heftangaben bei Artikeln, die über mehrere Ausgaben verteilt erschienen sind
* [Analyzing_WikidataItems.ipynb](Notebooks/Analyzing_WikidataItems.ipynb) - Analysen der bereits mit Wikidata verknüpften Gartenlaube-Artikel hinsichtlich Datenqualität
* [RIS_Export-Gartenlaube_Krieg1870.ipynb](Notebooks/RIS_Export-Gartenlaube_Krieg1870.ipynb) - RIS-Export von Gartenlaube-Artikeln zum Deutsch-Französischen Krieg 1870/71


## Queries
* [Die Stadt- oder Siedlungsschnecke](queries/Stadtschnecke.sparql) - Räumliche Verteilung der Inhalte der Gartenlaube Artikel
* [weihnachten](queries/Weihnachten.sparql) - Abfrage aller Artikel mit Bezug zu Weihnachten per Schlagwort und Titelheuristik. 
* [Brehms Reiseberichte](queries/Brehms_Travelogue.sparql) Timeline der naturkundlichen Berichte Alfred Brehms in der Gartenlaube.
* Carl Ernst Bock: Gesundheitsratgeber mit Wikicite, #Bocknetz > https://w.wiki/HCr sowie (erweitert) #BockHatQuery > https://w.wiki/HdS  

## Further information
* https://de.wikisource.org/wiki/Wikisource:Wikidata 
* https://blog.wikimedia.de/2019/10/16/hilfe-fuer-die-datenlaube-mit-wikisourcewikidata-die-freie-quellensammlung-verbessern/
* https://www.wikidata.org/wiki/Wikidata:WikiCite_Satellite_Cologne_2020/Submission/DieDatenlaube
