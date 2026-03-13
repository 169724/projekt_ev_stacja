
"""Modele danych aplikacji."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass(slots=True)
class ParametryStacji:
    """Parametry techniczne stacji ładowania."""

    liczba_ladowarek: int
    typ_ladowarki: str
    moc_ladowarki_kw: float
    limit_mocy_stacji_kw: float
    sprawnosc: float
    napiecie_v: int
    cos_phi: float = 0.98

    def as_dict(self) -> dict[str, Any]:
        return {
            "liczba_ladowarek": self.liczba_ladowarek,
            "typ_ladowarki": self.typ_ladowarki,
            "moc_ladowarki_kw": self.moc_ladowarki_kw,
            "limit_mocy_stacji_kw": self.limit_mocy_stacji_kw,
            "sprawnosc": self.sprawnosc,
            "napiecie_v": self.napiecie_v,
            "cos_phi": self.cos_phi,
        }


@dataclass(slots=True)
class ParametryGeneracjiPojazdow:
    """Parametry generatora pojazdów i sesji."""

    liczba_sesji: int
    miks_pojazdow: str
    soc_poczatkowy_min: float
    soc_poczatkowy_max: float
    soc_docelowy: float
    maks_czas_oczekiwania_min: int
    ziarno: int = 42

    def as_dict(self) -> dict[str, Any]:
        return {
            "liczba_sesji": self.liczba_sesji,
            "miks_pojazdow": self.miks_pojazdow,
            "soc_poczatkowy_min": self.soc_poczatkowy_min,
            "soc_poczatkowy_max": self.soc_poczatkowy_max,
            "soc_docelowy": self.soc_docelowy,
            "maks_czas_oczekiwania_min": self.maks_czas_oczekiwania_min,
            "ziarno": self.ziarno,
        }


@dataclass(slots=True)
class DefinicjaScenariusza:
    """Parametry scenariusza symulacyjnego."""

    identyfikator: str
    nazwa: str
    pora_roku: str
    typ_dnia: str
    wspolczynnik_naplywu: float
    wspolczynnik_temperatury_mocy: float
    wspolczynnik_energii: float
    opis: str
    profil_godzinowy: list[float]

    def as_dict(self) -> dict[str, Any]:
        return {
            "identyfikator": self.identyfikator,
            "nazwa": self.nazwa,
            "pora_roku": self.pora_roku,
            "typ_dnia": self.typ_dnia,
            "wspolczynnik_naplywu": self.wspolczynnik_naplywu,
            "wspolczynnik_temperatury_mocy": self.wspolczynnik_temperatury_mocy,
            "wspolczynnik_energii": self.wspolczynnik_energii,
            "opis": self.opis,
            "profil_godzinowy": self.profil_godzinowy,
        }


@dataclass(slots=True)
class SesjaPojazdu:
    """Pojedyncza sesja ładowania."""

    identyfikator: str
    nazwa_pojazdu: str
    segment: str
    pojemnosc_baterii_kwh: float
    ac_max_kw: float
    dc_max_kw: float
    soc_poczatkowy: float
    soc_docelowy: float
    krok_przyjazdu: int
    maks_czas_oczekiwania_min: int
    energia_do_uzupelnienia_kwh: float
    soc_biezacy: float = 0.0
    energia_dostarczona_kwh: float = 0.0
    czas_oczekiwania_min: float = 0.0
    czas_ladowania_min: float = 0.0
    krok_rozpoczecia: int | None = None
    krok_zakonczenia: int | None = None
    status: str = "oczekuje"
    slot_ladowarki: int | None = None

    def __post_init__(self) -> None:
        self.soc_biezacy = self.soc_poczatkowy


@dataclass(slots=True)
class WynikSymulacji:
    """Pakiet wyników pojedynczego scenariusza."""

    scenariusz: DefinicjaScenariusza
    profil_czasowy: pd.DataFrame
    sesje: pd.DataFrame
    zdarzenia: pd.DataFrame
    podsumowanie: dict[str, Any]
    wejscie: dict[str, Any]
    analiza_statystyczna: pd.DataFrame = field(default_factory=pd.DataFrame)
