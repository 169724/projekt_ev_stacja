
"""Eksport wyników symulacji do CSV, JSON i Markdown."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from app.models import WynikSymulacji


class EksporterWynikow:
    """Zapisuje wyniki wielu scenariuszy do jednego katalogu eksportu."""

    def __init__(self, katalog_projektu: Path) -> None:
        self.katalog_projektu = katalog_projektu
        self.katalog_eksportu = katalog_projektu / "exports"
        self.katalog_eksportu.mkdir(parents=True, exist_ok=True)

    def eksportuj(self, wyniki: dict[str, WynikSymulacji], nazwa_prefix: str = "wyniki") -> Path:
        znacznik = datetime.now().strftime("%Y%m%d_%H%M%S")
        katalog_docelowy = self.katalog_eksportu / f"{nazwa_prefix}_{znacznik}"
        katalog_docelowy.mkdir(parents=True, exist_ok=True)

        podsumowania = []
        wejscie = {}

        for identyfikator, wynik in wyniki.items():
            katalog_sc = katalog_docelowy / identyfikator
            katalog_sc.mkdir(exist_ok=True)

            wynik.profil_czasowy.to_csv(katalog_sc / "profil_czasowy.csv", index=False)
            wynik.sesje.to_csv(katalog_sc / "sesje.csv", index=False)
            wynik.zdarzenia.to_csv(katalog_sc / "zdarzenia.csv", index=False)
            wynik.analiza_statystyczna.to_csv(katalog_sc / "analiza_statystyczna.csv", index=False)

            podsumowania.append(wynik.podsumowanie)
            wejscie[identyfikator] = wynik.wejscie

        pd.DataFrame(podsumowania).to_csv(katalog_docelowy / "podsumowanie_scenariuszy.csv", index=False)

        with (katalog_docelowy / "wejscie.json").open("w", encoding="utf-8") as plik:
            json.dump(wejscie, plik, ensure_ascii=False, indent=2)

        raport_md = self._zbuduj_raport_markdown(wyniki)
        (katalog_docelowy / "raport.md").write_text(raport_md, encoding="utf-8")
        return katalog_docelowy

    def _zbuduj_raport_markdown(self, wyniki: dict[str, WynikSymulacji]) -> str:
        linie = [
            "# Raport z symulacji stacji ładowania EV",
            "",
            "Poniżej znajduje się uproszczony raport tekstowy wygenerowany automatycznie przez aplikację.",
            "",
        ]

        for wynik in wyniki.values():
            p = wynik.podsumowanie
            linie.extend(
                [
                    f"## {p['scenariusz']}",
                    "",
                    f"- Liczba sesji wygenerowanych: **{p['liczba_sesji_wygenerowanych']}**",
                    f"- Sesje zakończone: **{p['sesje_zakonczone']}**",
                    f"- Rezygnacje: **{p['sesje_rezygnacja']}**",
                    f"- Moc szczytowa: **{p['moc_szczytowa_kw']} kW**",
                    f"- Prąd szczytowy: **{p['prad_szczytowy_a']} A**",
                    f"- Średni czas oczekiwania: **{p['sredni_czas_oczekiwania_min']} min**",
                    f"- Średni czas ładowania: **{p['sredni_czas_ladowania_min']} min**",
                    f"- Energia całkowita: **{p['energia_calkowita_kwh']} kWh**",
                    f"- Maksymalna długość kolejki: **{p['max_kolejka']}**",
                    "",
                    "### Krótka interpretacja",
                    "",
                    (
                        "Wynik pokazuje wpływ scenariusza pogodowo-ruchowego na obciążenie stacji, "
                        "czas oczekiwania i stopień wykorzystania ładowarek."
                    ),
                    "",
                ]
            )
        return "\n".join(linie)
