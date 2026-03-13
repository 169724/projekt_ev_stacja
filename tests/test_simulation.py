from pathlib import Path

from app.core.simulation import SymulatorStacjiEV
from app.data_processing.data_loader import wczytaj_pojazdy_przetworzone, wczytaj_scenariusze
from app.models import ParametryGeneracjiPojazdow, ParametryStacji


def test_symulacja_generuje_niepuste_wyniki():
    katalog = Path(__file__).resolve().parents[1]
    pojazdy = wczytaj_pojazdy_przetworzone(katalog)
    scenariusz = wczytaj_scenariusze(katalog)["lato_dzien_roboczy"]

    stacja = ParametryStacji(
        liczba_ladowarek=4,
        typ_ladowarki="DC",
        moc_ladowarki_kw=150.0,
        limit_mocy_stacji_kw=450.0,
        sprawnosc=0.94,
        napiecie_v=400,
    )
    param = ParametryGeneracjiPojazdow(
        liczba_sesji=18,
        miks_pojazdow="Zróżnicowana",
        soc_poczatkowy_min=0.15,
        soc_poczatkowy_max=0.45,
        soc_docelowy=0.80,
        maks_czas_oczekiwania_min=45,
        ziarno=123,
    )

    wynik = SymulatorStacjiEV(krok_min=15).uruchom(stacja, param, scenariusz, pojazdy)
    assert not wynik.profil_czasowy.empty
    assert not wynik.sesje.empty
    assert "moc_szczytowa_kw" in wynik.podsumowanie
    assert wynik.podsumowanie["liczba_sesji_wygenerowanych"] > 0
