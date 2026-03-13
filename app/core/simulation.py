
"""Silnik symulacji zdarzeń dla stacji ładowania EV."""

from __future__ import annotations

from dataclasses import asdict
from math import ceil
from typing import Iterable

import numpy as np
import pandas as pd

from app.core.current_power import oblicz_moc_pojazdu_kw, oblicz_prad_calkowity
from app.models import (
    DefinicjaScenariusza,
    ParametryGeneracjiPojazdow,
    ParametryStacji,
    SesjaPojazdu,
    WynikSymulacji,
)


def formatuj_czas_z_kroku(krok: int, krok_min: int) -> str:
    """Konwersja kroku symulacji na zapis HH:MM."""
    minuty = int(max(0, krok) * krok_min)
    godzina = (minuty // 60) % 24
    minuta = minuty % 60
    return f"{godzina:02d}:{minuta:02d}"


def wybierz_flote(df_pojazdy: pd.DataFrame, miks_pojazdow: str) -> pd.DataFrame:
    """Filtruje flotę zgodnie z prostą etykietą z GUI."""
    miks = miks_pojazdow.lower()
    if "miejska" in miks:
        wynik = df_pojazdy[df_pojazdy["pojemnosc_baterii_kwh"] <= 50.0]
        return wynik if not wynik.empty else df_pojazdy
    if "szybkie" in miks:
        wynik = df_pojazdy[df_pojazdy["dc_max_kw"] >= 140.0]
        return wynik if not wynik.empty else df_pojazdy
    return df_pojazdy


def generuj_sesje(
    pojazdy_df: pd.DataFrame,
    parametry_pojazdow: ParametryGeneracjiPojazdow,
    scenariusz: DefinicjaScenariusza,
    krok_min: int,
) -> list[SesjaPojazdu]:
    """Tworzy listę syntetycznych sesji opartych na realnych źródłach i prostych założeniach."""
    rng = np.random.default_rng(parametry_pojazdow.ziarno)
    liczba_sesji = max(1, int(round(parametry_pojazdow.liczba_sesji * scenariusz.wspolczynnik_naplywu)))
    profil = np.array(scenariusz.profil_godzinowy, dtype=float)
    profil = profil / profil.sum()
    kroki_na_godzine = int(60 / krok_min)

    flota = wybierz_flote(pojazdy_df, parametry_pojazdow.miks_pojazdow).copy()
    if flota.empty:
        flota = pojazdy_df.copy()

    if "udzial_w_miksie" in flota.columns:
        wagi = flota["udzial_w_miksie"].fillna(1.0).to_numpy(dtype=float)
        wagi = wagi / wagi.sum()
    else:
        wagi = None

    sesje: list[SesjaPojazdu] = []
    indeksy = rng.choice(flota.index.to_numpy(), size=liczba_sesji, replace=True, p=wagi)

    for numer, idx in enumerate(indeksy, start=1):
        rekord = flota.loc[idx]
        godzina = int(rng.choice(np.arange(24), p=profil))
        przesuniecie = int(rng.integers(0, kroki_na_godzine))
        krok_przyjazdu = godzina * kroki_na_godzine + przesuniecie

        soc_min = min(parametry_pojazdow.soc_poczatkowy_min, parametry_pojazdow.soc_poczatkowy_max)
        soc_max = max(parametry_pojazdow.soc_poczatkowy_min, parametry_pojazdow.soc_poczatkowy_max)
        soc_poczatkowy = float(rng.uniform(soc_min, soc_max))

        base_target = float(parametry_pojazdow.soc_docelowy)
        delta_target = float(rng.uniform(-0.04, 0.03))
        soc_docelowy = min(0.95, max(soc_poczatkowy + 0.12, base_target + delta_target))

        wsp_energii = scenariusz.wspolczynnik_energii
        energia = rekord["pojemnosc_baterii_kwh"] * max(0.0, soc_docelowy - soc_poczatkowy) * wsp_energii
        maks_wait = int(max(5, rng.normal(parametry_pojazdow.maks_czas_oczekiwania_min, 8)))

        sesje.append(
            SesjaPojazdu(
                identyfikator=f"EV-{numer:03d}",
                nazwa_pojazdu=str(rekord["nazwa_pojazdu"]),
                segment=str(rekord["segment"]),
                pojemnosc_baterii_kwh=float(rekord["pojemnosc_baterii_kwh"]),
                ac_max_kw=float(rekord["ac_max_kw"]),
                dc_max_kw=float(rekord["dc_max_kw"]),
                soc_poczatkowy=round(soc_poczatkowy, 3),
                soc_docelowy=round(soc_docelowy, 3),
                krok_przyjazdu=int(krok_przyjazdu),
                maks_czas_oczekiwania_min=int(maks_wait),
                energia_do_uzupelnienia_kwh=round(float(energia), 3),
            )
        )

    sesje.sort(key=lambda x: (x.krok_przyjazdu, x.identyfikator))
    return sesje


def _loguj(zdarzenia: list[dict], krok: int, krok_min: int, sesja: SesjaPojazdu, zdarzenie: str, opis: str) -> None:
    zdarzenia.append(
        {
            "czas": formatuj_czas_z_kroku(krok, krok_min),
            "krok": krok,
            "sesja_id": sesja.identyfikator,
            "pojazd": sesja.nazwa_pojazdu,
            "zdarzenie": zdarzenie,
            "opis": opis,
        }
    )


class SymulatorStacjiEV:
    """Prosty, czytelny symulator do projektu studenckiego."""

    def __init__(self, krok_min: int = 15) -> None:
        self.krok_min = krok_min
        self.kroki_na_dobe = int(24 * 60 / krok_min)
        self.dt_h = krok_min / 60.0

    def uruchom(
        self,
        parametry_stacji: ParametryStacji,
        parametry_pojazdow: ParametryGeneracjiPojazdow,
        scenariusz: DefinicjaScenariusza,
        pojazdy_df: pd.DataFrame,
    ) -> WynikSymulacji:
        sesje = generuj_sesje(pojazdy_df, parametry_pojazdow, scenariusz, self.krok_min)
        sesje_po_id = {sesja.identyfikator: sesja for sesja in sesje}
        kolejka: list[SesjaPojazdu] = []
        aktywne: dict[str, SesjaPojazdu] = {}
        sloty: list[str | None] = [None] * parametry_stacji.liczba_ladowarek
        zdarzenia: list[dict] = []
        profil: list[dict] = []

        przyjazdy_na_krok: dict[int, list[SesjaPojazdu]] = {}
        for sesja in sesje:
            przyjazdy_na_krok.setdefault(sesja.krok_przyjazdu, []).append(sesja)

        for krok in range(self.kroki_na_dobe):
            # 1. Przyjazdy
            for sesja in przyjazdy_na_krok.get(krok, []):
                sesja.status = "w_kolejce"
                kolejka.append(sesja)
                _loguj(zdarzenia, krok, self.krok_min, sesja, "przyjazd", "Pojazd przyjechał na stację.")

            # 2. Rezygnacje z kolejki
            nowa_kolejka: list[SesjaPojazdu] = []
            for sesja in kolejka:
                czas_oczekiwania = (krok - sesja.krok_przyjazdu) * self.krok_min
                if czas_oczekiwania > sesja.maks_czas_oczekiwania_min:
                    sesja.czas_oczekiwania_min = float(czas_oczekiwania)
                    sesja.krok_zakonczenia = krok
                    sesja.status = "rezygnacja"
                    _loguj(
                        zdarzenia,
                        krok,
                        self.krok_min,
                        sesja,
                        "rezygnacja",
                        f"Przekroczono maksymalny czas oczekiwania: {sesja.maks_czas_oczekiwania_min} min.",
                    )
                else:
                    nowa_kolejka.append(sesja)
            kolejka = nowa_kolejka

            # 3. Przydział wolnych ładowarek
            for numer_slotu, zajety_przez in enumerate(sloty):
                if zajety_przez is not None or not kolejka:
                    continue
                sesja = kolejka.pop(0)
                sesja.krok_rozpoczecia = krok
                sesja.czas_oczekiwania_min = float((krok - sesja.krok_przyjazdu) * self.krok_min)
                sesja.status = "ladowanie"
                sesja.slot_ladowarki = numer_slotu
                sloty[numer_slotu] = sesja.identyfikator
                aktywne[sesja.identyfikator] = sesja
                _loguj(
                    zdarzenia,
                    krok,
                    self.krok_min,
                    sesja,
                    "start_ladowania",
                    f"Rozpoczęto sesję na ładowarce nr {numer_slotu + 1}.",
                )

            # 4. Obliczenie zapotrzebowania na moc
            zapotrzebowanie: dict[str, float] = {}
            for sesja_id, sesja in aktywne.items():
                moc_pojazdu = sesja.ac_max_kw if parametry_stacji.typ_ladowarki.upper() == "AC" else sesja.dc_max_kw
                moc_z_taperu = oblicz_moc_pojazdu_kw(
                    sesja.soc_biezacy,
                    parametry_stacji.typ_ladowarki,
                    moc_pojazdu,
                    parametry_stacji.moc_ladowarki_kw,
                    scenariusz.wspolczynnik_temperatury_mocy,
                )
                pozostala_energia = max(0.0, sesja.energia_do_uzupelnienia_kwh - sesja.energia_dostarczona_kwh)
                if pozostala_energia <= 0:
                    continue
                maks_moc_z_energii = pozostala_energia / max(1e-9, (self.dt_h * parametry_stacji.sprawnosc))
                zapotrzebowanie[sesja_id] = min(moc_z_taperu, maks_moc_z_energii)

            suma_zapotrzebowania = sum(zapotrzebowanie.values())
            if suma_zapotrzebowania > 0:
                wsp_skalowania = min(1.0, parametry_stacji.limit_mocy_stacji_kw / suma_zapotrzebowania)
            else:
                wsp_skalowania = 1.0

            przydzielona_moc = {sesja_id: moc * wsp_skalowania for sesja_id, moc in zapotrzebowanie.items()}
            moc_calkowita_kw = sum(przydzielona_moc.values())

            do_zamkniecia: list[SesjaPojazdu] = []
            for sesja_id, sesja in list(aktywne.items()):
                moc_grid = przydzielona_moc.get(sesja_id, 0.0)
                energia_do_baterii = moc_grid * parametry_stacji.sprawnosc * self.dt_h
                sesja.energia_dostarczona_kwh += energia_do_baterii
                sesja.soc_biezacy = min(
                    sesja.soc_docelowy,
                    sesja.soc_biezacy + energia_do_baterii / max(1e-9, sesja.pojemnosc_baterii_kwh),
                )
                sesja.czas_ladowania_min += self.krok_min

                if abs(moc_grid) > 0:
                    _loguj(
                        zdarzenia,
                        krok,
                        self.krok_min,
                        sesja,
                        "zmiana_mocy",
                        f"Moc chwilowa: {moc_grid:.1f} kW, SOC: {sesja.soc_biezacy:.3f}.",
                    )

                if (
                    sesja.energia_dostarczona_kwh >= sesja.energia_do_uzupelnienia_kwh - 0.02
                    or sesja.soc_biezacy >= sesja.soc_docelowy - 0.002
                ):
                    sesja.krok_zakonczenia = krok + 1
                    sesja.status = "zakonczona"
                    do_zamkniecia.append(sesja)

            for sesja in do_zamkniecia:
                if sesja.slot_ladowarki is not None:
                    sloty[sesja.slot_ladowarki] = None
                aktywne.pop(sesja.identyfikator, None)
                _loguj(
                    zdarzenia,
                    krok + 1,
                    self.krok_min,
                    sesja,
                    "koniec_ladowania",
                    f"Sesja zakończona. Dostarczono {sesja.energia_dostarczona_kwh:.2f} kWh.",
                )

            prad_calkowity_a = oblicz_prad_calkowity(
                moc_calkowita_kw,
                parametry_stacji.typ_ladowarki,
                parametry_stacji.napiecie_v,
                parametry_stacji.cos_phi,
            )
            profil.append(
                {
                    "czas": formatuj_czas_z_kroku(krok, self.krok_min),
                    "krok": krok,
                    "moc_calkowita_kw": round(moc_calkowita_kw, 3),
                    "prad_calkowity_a": round(prad_calkowity_a, 3),
                    "aktywne_sesje": len(aktywne),
                    "kolejka": len(kolejka),
                    "wykorzystanie_ladowarek_proc": round(
                        100.0 * len(aktywne) / max(1, parametry_stacji.liczba_ladowarek), 2
                    ),
                }
            )

        # 5. Domknięcie sesji, które nie zdążyły się zakończyć w horyzoncie 24h
        for sesja in aktywne.values():
            sesja.krok_zakonczenia = self.kroki_na_dobe
            sesja.status = "niedokonczona"
            _loguj(
                zdarzenia,
                self.kroki_na_dobe,
                self.krok_min,
                sesja,
                "koniec_horyzontu",
                "Doba symulacji zakończyła się przed ukończeniem ładowania.",
            )

        for sesja in kolejka:
            sesja.krok_zakonczenia = self.kroki_na_dobe
            sesja.status = "niedokonczona_w_kolejce"
            sesja.czas_oczekiwania_min = float((self.kroki_na_dobe - sesja.krok_przyjazdu) * self.krok_min)
            _loguj(
                zdarzenia,
                self.kroki_na_dobe,
                self.krok_min,
                sesja,
                "koniec_horyzontu",
                "Pojazd pozostał w kolejce do końca doby.",
            )

        sesje_df = self._buduj_df_sesji(sesje)
        profil_df = pd.DataFrame(profil)
        zdarzenia_df = pd.DataFrame(zdarzenia)
        podsumowanie = self._policz_podsumowanie(profil_df, sesje_df, scenariusz, parametry_stacji, parametry_pojazdow)
        analiza = self._analiza_statystyczna(sesje_df)

        wejscie = {
            "stacja": parametry_stacji.as_dict(),
            "pojazdy": parametry_pojazdow.as_dict(),
            "scenariusz": scenariusz.as_dict(),
        }
        return WynikSymulacji(
            scenariusz=scenariusz,
            profil_czasowy=profil_df,
            sesje=sesje_df,
            zdarzenia=zdarzenia_df,
            podsumowanie=podsumowanie,
            wejscie=wejscie,
            analiza_statystyczna=analiza,
        )

    def _buduj_df_sesji(self, sesje: Iterable[SesjaPojazdu]) -> pd.DataFrame:
        """Tworzy tabelę sesji gotową do GUI i eksportu."""
        rekordy: list[dict] = []
        for sesja in sesje:
            rekordy.append(
                {
                    "sesja_id": sesja.identyfikator,
                    "pojazd": sesja.nazwa_pojazdu,
                    "segment": sesja.segment,
                    "pojemnosc_baterii_kwh": round(sesja.pojemnosc_baterii_kwh, 2),
                    "soc_poczatkowy": round(sesja.soc_poczatkowy, 3),
                    "soc_docelowy": round(sesja.soc_docelowy, 3),
                    "soc_koncowy": round(sesja.soc_biezacy, 3),
                    "przyjazd": formatuj_czas_z_kroku(sesja.krok_przyjazdu, self.krok_min),
                    "start_ladowania": (
                        formatuj_czas_z_kroku(sesja.krok_rozpoczecia, self.krok_min)
                        if sesja.krok_rozpoczecia is not None
                        else "-"
                    ),
                    "koniec_ladowania": (
                        formatuj_czas_z_kroku(sesja.krok_zakonczenia, self.krok_min)
                        if sesja.krok_zakonczenia is not None
                        else "-"
                    ),
                    "czas_oczekiwania_min": round(sesja.czas_oczekiwania_min, 2),
                    "czas_ladowania_min": round(sesja.czas_ladowania_min, 2),
                    "energia_planowana_kwh": round(sesja.energia_do_uzupelnienia_kwh, 3),
                    "energia_dostarczona_kwh": round(sesja.energia_dostarczona_kwh, 3),
                    "slot_ladowarki": sesja.slot_ladowarki + 1 if sesja.slot_ladowarki is not None else "-",
                    "status": sesja.status,
                }
            )
        return pd.DataFrame(rekordy)

    def _policz_podsumowanie(
        self,
        profil_df: pd.DataFrame,
        sesje_df: pd.DataFrame,
        scenariusz: DefinicjaScenariusza,
        parametry_stacji: ParametryStacji,
        parametry_pojazdow: ParametryGeneracjiPojazdow,
    ) -> dict[str, float | int | str]:
        """Tworzy główne wskaźniki do sekcji wyników liczbowych."""
        zakonczone = sesje_df[sesje_df["status"] == "zakonczona"]
        rozpoczte = sesje_df[sesje_df["status"].isin(["zakonczona", "niedokonczona"])]

        sredni_wait = float(rozpoczte["czas_oczekiwania_min"].mean()) if not rozpoczte.empty else 0.0
        sredni_charge = float(rozpoczte["czas_ladowania_min"].mean()) if not rozpoczte.empty else 0.0
        srednia_energia = float(zakonczone["energia_dostarczona_kwh"].mean()) if not zakonczone.empty else 0.0

        return {
            "scenariusz": scenariusz.nazwa,
            "liczba_sesji_wygenerowanych": int(len(sesje_df)),
            "sesje_zakonczone": int((sesje_df["status"] == "zakonczona").sum()),
            "sesje_rezygnacja": int((sesje_df["status"] == "rezygnacja").sum()),
            "sesje_niedokonczone": int((sesje_df["status"] == "niedokonczona").sum()),
            "sesje_niedokonczone_w_kolejce": int((sesje_df["status"] == "niedokonczona_w_kolejce").sum()),
            "moc_szczytowa_kw": round(float(profil_df["moc_calkowita_kw"].max()), 3),
            "prad_szczytowy_a": round(float(profil_df["prad_calkowity_a"].max()), 3),
            "srednia_moc_kw": round(float(profil_df["moc_calkowita_kw"].mean()), 3),
            "max_kolejka": int(profil_df["kolejka"].max()),
            "sredni_czas_oczekiwania_min": round(sredni_wait, 3),
            "sredni_czas_ladowania_min": round(sredni_charge, 3),
            "srednia_energia_na_sesje_kwh": round(srednia_energia, 3),
            "energia_calkowita_kwh": round(float(sesje_df["energia_dostarczona_kwh"].sum()), 3),
            "wykorzystanie_ladowarek_proc": round(float(profil_df["wykorzystanie_ladowarek_proc"].mean()), 3),
            "typ_ladowarki": parametry_stacji.typ_ladowarki,
            "limit_mocy_stacji_kw": parametry_stacji.limit_mocy_stacji_kw,
            "liczba_ladowarek": parametry_stacji.liczba_ladowarek,
            "liczba_sesji_bazowa": parametry_pojazdow.liczba_sesji,
        }

    def _analiza_statystyczna(self, sesje_df: pd.DataFrame) -> pd.DataFrame:
        """Zestaw prostych statystyk opisowych do raportu i GUI."""
        if sesje_df.empty:
            return pd.DataFrame(columns=["miara", "wartosc"])

        metryki = {
            "średni czas oczekiwania [min]": sesje_df["czas_oczekiwania_min"].mean(),
            "mediana czasu oczekiwania [min]": sesje_df["czas_oczekiwania_min"].median(),
            "odchylenie czasu oczekiwania [min]": sesje_df["czas_oczekiwania_min"].std(ddof=0),
            "średni czas ładowania [min]": sesje_df["czas_ladowania_min"].mean(),
            "mediana czasu ładowania [min]": sesje_df["czas_ladowania_min"].median(),
            "odchylenie czasu ładowania [min]": sesje_df["czas_ladowania_min"].std(ddof=0),
            "średnia energia na sesję [kWh]": sesje_df["energia_dostarczona_kwh"].mean(),
            "mediana energii na sesję [kWh]": sesje_df["energia_dostarczona_kwh"].median(),
            "odchylenie energii [kWh]": sesje_df["energia_dostarczona_kwh"].std(ddof=0),
        }
        return pd.DataFrame(
            [{"miara": nazwa, "wartosc": round(float(wartosc) if pd.notna(wartosc) else 0.0, 4)} for nazwa, wartosc in metryki.items()]
        )
