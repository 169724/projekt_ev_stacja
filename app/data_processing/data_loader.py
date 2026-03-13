
"""Wczytywanie konfiguracji, danych i dokumentacji."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from app.models import DefinicjaScenariusza


def wczytaj_json(sciezka: Path) -> dict:
    with sciezka.open("r", encoding="utf-8") as plik:
        return json.load(plik)


def wczytaj_pojazdy_przetworzone(katalog_projektu: Path) -> pd.DataFrame:
    sciezka = katalog_projektu / "data" / "processed" / "pojazdy_domyslne.csv"
    return pd.read_csv(sciezka)


def wczytaj_profile_scenariuszy(katalog_projektu: Path) -> pd.DataFrame:
    sciezka = katalog_projektu / "data" / "processed" / "profile_scenariuszy_godzinowe.csv"
    return pd.read_csv(sciezka)


def wczytaj_scenariusze(katalog_projektu: Path) -> dict[str, DefinicjaScenariusza]:
    df = wczytaj_profile_scenariuszy(katalog_projektu)
    scenariusze: dict[str, DefinicjaScenariusza] = {}
    for identyfikator, grupa in df.groupby("scenariusz"):
        grupa = grupa.sort_values("godzina")
        pierwszy = grupa.iloc[0]
        scenariusze[identyfikator] = DefinicjaScenariusza(
            identyfikator=identyfikator,
            nazwa=str(pierwszy["nazwa"]),
            pora_roku=str(pierwszy["pora_roku"]),
            typ_dnia=str(pierwszy["typ_dnia"]),
            wspolczynnik_naplywu=float(pierwszy["wspolczynnik_naplywu"]),
            wspolczynnik_temperatury_mocy=float(pierwszy["wspolczynnik_temperatury_mocy"]),
            wspolczynnik_energii=float(pierwszy["wspolczynnik_energii"]),
            opis=str(pierwszy["opis"]),
            profil_godzinowy=grupa["waga_przyjazdu"].astype(float).tolist(),
        )
    return scenariusze


def wczytaj_ustawienia(katalog_projektu: Path) -> dict:
    return wczytaj_json(katalog_projektu / "config" / "settings.json")


def wczytaj_markdown(sciezka: Path) -> str:
    return sciezka.read_text(encoding="utf-8")


def wczytaj_opis_danych(katalog_projektu: Path) -> str:
    opis = wczytaj_markdown(katalog_projektu / "docs" / "opis_danych.md")
    zrodla = wczytaj_markdown(katalog_projektu / "docs" / "zrodla_danych.md")
    return f"{opis}\n\n---\n\n{zrodla}"
