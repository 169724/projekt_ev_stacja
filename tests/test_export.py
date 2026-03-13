from pathlib import Path

from app.core.simulation import SymulatorStacjiEV
from app.data_processing.data_loader import wczytaj_pojazdy_przetworzone, wczytaj_scenariusze
from app.exporters.exporter import EksporterWynikow
from app.models import ParametryGeneracjiPojazdow, ParametryStacji


def test_eksport_tworzony_w_katalogu_tymczasowym(tmp_path):
    katalog = Path(__file__).resolve().parents[1]
    pojazdy = wczytaj_pojazdy_przetworzone(katalog)
    scenariusz = wczytaj_scenariusze(katalog)["zima_weekend"]

    stacja = ParametryStacji(
        liczba_ladowarek=3,
        typ_ladowarki="AC",
        moc_ladowarki_kw=11.0,
        limit_mocy_stacji_kw=22.0,
        sprawnosc=0.90,
        napiecie_v=400,
    )
    param = ParametryGeneracjiPojazdow(
        liczba_sesji=12,
        miks_pojazdow="Miejska AC",
        soc_poczatkowy_min=0.20,
        soc_poczatkowy_max=0.50,
        soc_docelowy=0.85,
        maks_czas_oczekiwania_min=35,
        ziarno=77,
    )

    wynik = SymulatorStacjiEV(krok_min=15).uruchom(stacja, param, scenariusz, pojazdy)

    eksporter = EksporterWynikow(tmp_path)
    katalog_doc = eksporter.eksportuj({"zima_weekend": wynik}, nazwa_prefix="test")

    assert (katalog_doc / "podsumowanie_scenariuszy.csv").exists()
    assert (katalog_doc / "wejscie.json").exists()
    assert (katalog_doc / "raport.md").exists()
    assert (katalog_doc / "zima_weekend" / "sesje.csv").exists()
