
"""Funkcje obliczające moc i prąd ładowania."""

from __future__ import annotations

import math


def ogranicz_udzial_soc(soc: float) -> float:
    """Pilnuje zakresu 0..1."""
    return max(0.0, min(1.0, soc))


def oblicz_prad_ac_trzyfazowy(moc_kw: float, napiecie_v: float = 400.0, cos_phi: float = 0.98) -> float:
    """
    Oblicza prąd dla ładowania AC 3-fazowego.

    Wzór:
    I = P / (sqrt(3) * U * cos(phi))
    """
    if moc_kw <= 0:
        return 0.0
    return (moc_kw * 1000.0) / (math.sqrt(3.0) * napiecie_v * cos_phi)


def oblicz_prad_dc(moc_kw: float, napiecie_v: float = 400.0) -> float:
    """
    Oblicza prąd dla ładowania DC.

    Wzór:
    I = P / U
    """
    if moc_kw <= 0:
        return 0.0
    return (moc_kw * 1000.0) / napiecie_v


def taper_dc(soc: float) -> float:
    """
    Przybliżony współczynnik ograniczenia mocy dla DC.

    Założenie:
    - do 60% SOC można utrzymywać moc bliską maksymalnej,
    - po 60% zaczyna się stopniowe ograniczanie,
    - po 80% ograniczenie jest wyraźne,
    - przy 95% moc jest już niewielka.
    """
    soc = ogranicz_udzial_soc(soc)
    if soc <= 0.60:
        return 1.00
    if soc <= 0.80:
        return 1.00 - ((soc - 0.60) / 0.20) * 0.40  # 1.00 -> 0.60
    if soc <= 0.95:
        return 0.60 - ((soc - 0.80) / 0.15) * 0.40  # 0.60 -> 0.20
    return 0.12


def taper_ac(soc: float) -> float:
    """
    Przybliżony współczynnik ograniczenia mocy dla AC.

    W ładowaniu AC przebieg bywa bardziej płaski niż w DC, ale
    pod sam koniec ładowania również maleje.
    """
    soc = ogranicz_udzial_soc(soc)
    if soc <= 0.90:
        return 1.00
    if soc <= 0.98:
        return 1.00 - ((soc - 0.90) / 0.08) * 0.45  # 1.00 -> 0.55
    return 0.40


def oblicz_moc_pojazdu_kw(
    soc: float,
    typ_ladowarki: str,
    moc_maks_pojazdu_kw: float,
    moc_maks_ladowarki_kw: float,
    wspolczynnik_temperatury: float = 1.0,
) -> float:
    """
    Zwraca chwilową moc, jaką pojazd jest w stanie przyjąć z punktu ładowania.
    """
    typ = typ_ladowarki.upper()
    soc = ogranicz_udzial_soc(soc)
    moc_bazowa = min(moc_maks_pojazdu_kw, moc_maks_ladowarki_kw)

    if typ == "AC":
        wsp_taper = taper_ac(soc)
    else:
        wsp_taper = taper_dc(soc)

    moc = moc_bazowa * wsp_taper * max(0.0, wspolczynnik_temperatury)
    return max(0.0, moc)


def oblicz_prad_calkowity(
    moc_kw: float,
    typ_ladowarki: str,
    napiecie_v: float,
    cos_phi: float = 0.98,
) -> float:
    """Wygodna funkcja obudowująca obliczenia prądu."""
    if typ_ladowarki.upper() == "AC":
        return oblicz_prad_ac_trzyfazowy(moc_kw, napiecie_v, cos_phi)
    return oblicz_prad_dc(moc_kw, napiecie_v)


def opis_funkcji_pradu_markdown() -> str:
    """Opis wzorów i założeń pokazywany w GUI oraz README."""
    return """
## Funkcja opisująca wartość prądu ładowania

W projekcie zastosowano prostą, czytelną funkcję mocy i prądu:

### 1. Ładowanie AC (trójfazowe)

\\[
I_{AC} = \\frac{P}{\\sqrt{3} \\cdot U \\cdot cos\\varphi}
\\]

gdzie:
- **P** – moc chwilowa [W],
- **U** – napięcie międzyfazowe [V],
- **cosφ** – współczynnik mocy (w projekcie domyślnie 0,98).

Dla AC przyjęto niemal płaski przebieg mocy aż do około 90% SOC,
a następnie łagodne zmniejszanie pod koniec sesji.

### 2. Ładowanie DC

\\[
I_{DC} = \\frac{P}{U}
\\]

Dla DC zastosowano uproszczony model taperingu:
- do 60% SOC: moc bliska maksimum,
- 60–80% SOC: stopniowy spadek,
- 80–95% SOC: silniejszy spadek,
- powyżej 95% SOC: moc niska.

### 3. Wpływ scenariusza

Chwilowa moc sesji:

\\[
P_{eff}(t) = min(P_{pojazd}, P_{ładowarka}) \\cdot k_{SOC}(t) \\cdot k_{temp}
\\]

gdzie:
- **k_SOC(t)** – współczynnik taperingu zależny od SOC,
- **k_temp** – współczynnik temperaturowy scenariusza.

W scenariuszach zimowych przyjęto niższy współczynnik temperaturowy,
aby odtworzyć wolniejsze ładowanie przy niskiej temperaturze.
"""
