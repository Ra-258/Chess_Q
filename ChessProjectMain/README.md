# ChessProjectMain

Jednoduchá desktopová šachová hra vytvořená v Pythonu 3.12 pomocí
Tkinteru jako projekt do programovacího semináře.

## Spuštění

1.  Rozbal ZIP archiv.
2.  Otevři složku `ChessProjectMain` v PyCharmu.
3.  Nastav Python 3.12 jako interpreter.
4.  Spusť soubor `main.py`.

Hru lze spustit také z terminálu:

``` bash
py -3.12 main.py
```

Není potřeba instalovat žádné další knihovny.

## Funkce

-   Hra proti počítači se třemi obtížnostmi (Easy, Medium, Hard).
-   Hra dvou hráčů na jednom počítači.
-   Výběr barvy figurek nebo náhodná volba.
-   Časové limity včetně režimu bez časového omezení.
-   Základní šachová pravidla včetně rošády, en passant a proměny pěšce.
-   Detekce šachu a matu.
-   Vrácení tahu (Undo), historie tahů a otočení šachovnice.
-   Premove pro přípravu tahu během přemýšlení počítače.
-   Ukládání a pokračování rozehrané partie.
-   Osm volitelných šachových úkolů (Quests).
-   Nastavení vzhledu a chování hry.

## Struktura projektu

  Soubor / složka   Popis
  ----------------- ---------------------------------
  `main.py`         Spuštění aplikace
  `gui.py`          Grafické rozhraní a ovládání
  `engine.py`       Šachová pravidla a herní logika
  `ai.py`           Herní logika počítače
  `clock.py`        Herní čas
  `storage.py`      Ukládání dat a nastavení
  `quests.py`       Správa šachových úkolů
  `assets/`         Grafické podklady
  `tests/`          Automatické testy

Projekt využívá objektově orientované programování, třídy, podmínky,
cykly, seznamy a práci se soubory JSON.

Počítačový soupeř používá vlastní jednoduchý algoritmus pro výběr tahů.
Nevyužívá externí šachové enginy ani online služby.

## Ukládání dat

Nastavení, rozehraná partie a postup v úkolech se ukládají do složky:

``` text
%USERPROFILE%\.chessprojectmain
```

Data zůstávají zachována i po zavření aplikace.

## Testy

Testy lze spustit z kořenové složky projektu příkazem:

``` bash
py -3.12 -m unittest discover -s tests -v
```

Testy grafického rozhraní vyžadují dostupné grafické prostředí.

## GitHub

Pro nahrání projektu do vlastního forku `Chess_Q` nahraď obsah
projektové složky soubory z `ChessProjectMain`.

Ponech složku `.git` a do commitu nezahrnuj zejména:

-   `.venv`
-   `.idea`
-   `__pycache__`
-   vlastní uložené partie a nastavení

Poté proveď commit a push.

## Grafické podklady

Grafické podklady byly vytvořeny pomocí AI nástroje ChatGPT.
