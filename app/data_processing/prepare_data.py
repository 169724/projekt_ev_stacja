
"""Skrypt przygotowujący dane przetworzone z plików raw."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def przygotuj_pojazdy(raw_df: pd.DataFrame) -> pd.DataFrame:
    wynik = raw_df.copy()

    # AC: jeśli w źródle nie ma jawnej mocy AC, wyliczamy ją z pojemności baterii i czasu 0-100%.
    wynik["ac_max_kw"] = wynik["oficjalna_moc_ac_kw"]
    mask_ac = wynik["ac_max_kw"].isna()
    wynik.loc[mask_ac, "ac_max_kw"] = (
        wynik.loc[mask_ac, "pojemnosc_baterii_kwh"] / wynik.loc[mask_ac, "czas_ac_0_100_h"]
    ).round(1)

    # DC: jeśli nie ma jawnej mocy pojazdu, szacujemy ją z energii 10-80% oraz czasu.
    # Dla profilu z taperingiem przyjęto współczynnik 1.4 względem średniej mocy.
    wynik["dc_max_kw"] = wynik["oficjalna_moc_dc_kw"]
    mask_dc = wynik["dc_max_kw"].isna()
    srednia_moc_10_80 = (
        wynik.loc[mask_dc, "pojemnosc_baterii_kwh"] * 0.7 / (wynik.loc[mask_dc, "czas_dc_10_80_min"] / 60.0)
    )
    wynik.loc[mask_dc, "dc_max_kw"] = np.minimum(
        wynik.loc[mask_dc, "moc_stacji_referencyjnej_dc_kw"],
        (srednia_moc_10_80 * 1.4).round(1),
    )

    wynik["udzial_w_miksie"] = [0.24, 0.20, 0.28, 0.28][: len(wynik)]
    wynik["status_danych"] = "przetworzone"
    wynik["uwaga_przetworzenie"] = np.where(
        raw_df["oficjalna_moc_dc_kw"].isna(),
        "dc_max_kw oszacowano z czasu 10-80% oraz mocy stacji referencyjnej",
        "dc_max_kw pochodzi bezpośrednio ze źródła oficjalnego",
    )

    kolumny = [
        "pojazd_id",
        "nazwa_pojazdu",
        "segment",
        "pojemnosc_baterii_kwh",
        "ac_max_kw",
        "dc_max_kw",
        "udzial_w_miksie",
        "zrodlo_nazwa",
        "zrodlo_url",
        "status_danych",
        "uwaga_przetworzenie",
    ]
    return wynik[kolumny]


def przygotuj_scenariusze() -> pd.DataFrame:
    weekday = np.array([
        0.02, 0.01, 0.01, 0.01, 0.02, 0.03, 0.05, 0.06, 0.07, 0.06, 0.05, 0.05,
        0.05, 0.05, 0.06, 0.07, 0.09, 0.10, 0.08, 0.06, 0.04, 0.03, 0.02, 0.01
    ])
    weekend = np.array([
        0.01, 0.005, 0.005, 0.005, 0.01, 0.015, 0.02, 0.03, 0.05, 0.06, 0.07, 0.08,
        0.09, 0.09, 0.08, 0.07, 0.06, 0.05, 0.04, 0.035, 0.025, 0.02, 0.015, 0.01
    ])
    weekday = weekday / weekday.sum()
    weekend = weekend / weekend.sum()

    definicje = [
        {
            "scenariusz": "lato_dzien_roboczy",
            "nazwa": "Lato - dzień roboczy",
            "pora_roku": "lato",
            "typ_dnia": "dzień roboczy",
            "wspolczynnik_naplywu": 1.08,
            "wspolczynnik_temperatury_mocy": 1.00,
            "wspolczynnik_energii": 1.02,
            "opis": "Mieszany profil miejsko-tranzytowy z wyższym ruchem popołudniowym.",
            "profil": weekday,
        },
        {
            "scenariusz": "lato_weekend",
            "nazwa": "Lato - weekend",
            "pora_roku": "lato",
            "typ_dnia": "weekend",
            "wspolczynnik_naplywu": 1.16,
            "wspolczynnik_temperatury_mocy": 1.00,
            "wspolczynnik_energii": 1.00,
            "opis": "Większy udział podróży rekreacyjnych i pik w środku dnia.",
            "profil": weekend,
        },
        {
            "scenariusz": "zima_dzien_roboczy",
            "nazwa": "Zima - dzień roboczy",
            "pora_roku": "zima",
            "typ_dnia": "dzień roboczy",
            "wspolczynnik_naplywu": 0.95,
            "wspolczynnik_temperatury_mocy": 0.85,
            "wspolczynnik_energii": 1.08,
            "opis": "Niższa temperatura ogranicza moc DC i nieco zwiększa zapotrzebowanie energetyczne.",
            "profil": weekday,
        },
        {
            "scenariusz": "zima_weekend",
            "nazwa": "Zima - weekend",
            "pora_roku": "zima",
            "typ_dnia": "weekend",
            "wspolczynnik_naplywu": 0.90,
            "wspolczynnik_temperatury_mocy": 0.82,
            "wspolczynnik_energii": 1.10,
            "opis": "Najmniejszy napływ i największe ograniczenie mocy wynikające z zimna.",
            "profil": weekend,
        },
    ]

    rekordy: list[dict] = []
    for definicja in definicje:
        for godzina, waga in enumerate(definicja["profil"]):
            rekordy.append(
                {
                    "scenariusz": definicja["scenariusz"],
                    "nazwa": definicja["nazwa"],
                    "pora_roku": definicja["pora_roku"],
                    "typ_dnia": definicja["typ_dnia"],
                    "godzina": godzina,
                    "waga_przyjazdu": round(float(waga), 6),
                    "wspolczynnik_naplywu": definicja["wspolczynnik_naplywu"],
                    "wspolczynnik_temperatury_mocy": definicja["wspolczynnik_temperatury_mocy"],
                    "wspolczynnik_energii": definicja["wspolczynnik_energii"],
                    "opis": definicja["opis"],
                    "metoda": (
                        "profil syntetyczny oparty na opisie godzinowych pików ruchu "
                        "z danych DfT oraz korektach sezonowych/temperaturowych opisanych w docs"
                    ),
                }
            )
    return pd.DataFrame(rekordy)


def uruchom_przygotowanie(katalog_projektu: Path) -> None:
    raw_path = katalog_projektu / "data" / "raw" / "pojazdy_ev_zrodla.csv"
    processed_vehicle_path = katalog_projektu / "data" / "processed" / "pojazdy_domyslne.csv"
    processed_scenario_path = katalog_projektu / "data" / "processed" / "profile_scenariuszy_godzinowe.csv"

    raw_df = pd.read_csv(raw_path)
    przygotuj_pojazdy(raw_df).to_csv(processed_vehicle_path, index=False)
    przygotuj_scenariusze().to_csv(processed_scenario_path, index=False)


if __name__ == "__main__":
    katalog = Path(__file__).resolve().parents[2]
    uruchom_przygotowanie(katalog)
    print("Dane przetworzone zostały zapisane.")
