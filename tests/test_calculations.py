from app.core.current_power import (
    oblicz_moc_pojazdu_kw,
    oblicz_prad_ac_trzyfazowy,
    oblicz_prad_dc,
    taper_dc,
)


def test_prad_ac_dla_11_kw():
    prad = oblicz_prad_ac_trzyfazowy(11.0, 400.0, 0.98)
    assert 15.5 < prad < 16.8


def test_prad_dc_dla_50_kw_i_400v():
    prad = oblicz_prad_dc(50.0, 400.0)
    assert prad == 125.0


def test_taper_dc_maleje_po_80_proc_soc():
    assert taper_dc(0.50) > taper_dc(0.85)


def test_moc_pojazdu_nie_przekracza_ladowarki():
    moc = oblicz_moc_pojazdu_kw(
        soc=0.35,
        typ_ladowarki="DC",
        moc_maks_pojazdu_kw=220.0,
        moc_maks_ladowarki_kw=150.0,
        wspolczynnik_temperatury=1.0,
    )
    assert moc <= 150.0
