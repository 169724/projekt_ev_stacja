"""Okno główne aplikacji GUI."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.charts.plot_manager import MenedzerWykresow, PlatnoWykresu
from app.core.current_power import opis_funkcji_pradu_markdown
from app.core.simulation import SymulatorStacjiEV
from app.data_processing.data_loader import (
    wczytaj_opis_danych,
    wczytaj_pojazdy_przetworzone,
    wczytaj_scenariusze,
    wczytaj_ustawienia,
)
from app.exporters.exporter import EksporterWynikow
from app.models import ParametryGeneracjiPojazdow, ParametryStacji


class GlowneOkno(QMainWindow):
    """Główne okno aplikacji."""

    def __init__(self, katalog_projektu: Path) -> None:
        super().__init__()
        self.katalog_projektu = katalog_projektu
        self.ustawienia = wczytaj_ustawienia(katalog_projektu)
        self.pojazdy_df = wczytaj_pojazdy_przetworzone(katalog_projektu)
        self.scenariusze = wczytaj_scenariusze(katalog_projektu)
        self.opis_danych_md = wczytaj_opis_danych(katalog_projektu)

        self.symulator = SymulatorStacjiEV(krok_min=self.ustawienia["krok_czasowy_min"])
        self.eksporter = EksporterWynikow(katalog_projektu)
        self.menedzer_wykresow = MenedzerWykresow()
        self.ostatnie_wyniki = {}
        self.mapowanie_wykresow = {
            "profil_mocy": "Profil mocy",
            "profil_pradu": "Profil prądu",
            "zajetosc_ladowarek": "Liczba zajętych ładowarek",
            "kolejka": "Długość kolejki",
            "histogram_czasu_ladowania": "Histogram czasu ładowania",
        }

        self.setWindowTitle(self.ustawienia["nazwa_aplikacji"])
        self.resize(1500, 900)
        self._zbuduj_ui()
        self._wczytaj_domyslne_wartosci()
        self._odswiez_tekst_zrodel()

    def _zbuduj_ui(self) -> None:
        centralny = QWidget()
        self.setCentralWidget(centralny)
        uklad_glowny = QHBoxLayout(centralny)

        panel_lewy = self._zbuduj_panel_sterowania()
        panel_prawy = self._zbuduj_panel_wynikow()

        uklad_glowny.addWidget(panel_lewy, 0)
        uklad_glowny.addWidget(panel_prawy, 1)

    def _zbuduj_panel_sterowania(self) -> QWidget:
        kontener = QWidget()
        uklad = QVBoxLayout(kontener)

        grupa_stacja = QGroupBox("Parametry stacji")
        form_stacja = QFormLayout(grupa_stacja)
        self.spin_ladowarki = QSpinBox()
        self.spin_ladowarki.setRange(1, 64)

        self.combo_typ = QComboBox()
        self.combo_typ.addItems(["AC", "DC"])

        self.spin_moc_ladowarki = QDoubleSpinBox()
        self.spin_moc_ladowarki.setRange(1.0, 500.0)
        self.spin_moc_ladowarki.setDecimals(1)
        self.spin_moc_ladowarki.setSuffix(" kW")

        self.spin_limit_mocy = QDoubleSpinBox()
        self.spin_limit_mocy.setRange(1.0, 5000.0)
        self.spin_limit_mocy.setDecimals(1)
        self.spin_limit_mocy.setSuffix(" kW")

        self.spin_sprawnosc = QDoubleSpinBox()
        self.spin_sprawnosc.setRange(0.50, 1.00)
        self.spin_sprawnosc.setDecimals(2)
        self.spin_sprawnosc.setSingleStep(0.01)

        self.spin_napiecie = QSpinBox()
        self.spin_napiecie.setRange(120, 1000)
        self.spin_napiecie.setSuffix(" V")

        form_stacja.addRow("Liczba ładowarek:", self.spin_ladowarki)
        form_stacja.addRow("Typ ładowarki:", self.combo_typ)
        form_stacja.addRow("Maks. moc jednej ładowarki:", self.spin_moc_ladowarki)
        form_stacja.addRow("Limit mocy całej stacji:", self.spin_limit_mocy)
        form_stacja.addRow("Sprawność:", self.spin_sprawnosc)
        form_stacja.addRow("Napięcie:", self.spin_napiecie)

        grupa_pojazdy = QGroupBox("Parametry pojazdów / generatora sesji")
        form_pojazdy = QFormLayout(grupa_pojazdy)

        self.spin_liczba_sesji = QSpinBox()
        self.spin_liczba_sesji.setRange(1, 500)

        self.combo_miks = QComboBox()
        self.combo_miks.addItems(["Zróżnicowana", "Miejska AC", "Szybkie DC"])

        self.spin_soc_min = QDoubleSpinBox()
        self.spin_soc_min.setRange(0.0, 1.0)
        self.spin_soc_min.setDecimals(2)
        self.spin_soc_min.setSingleStep(0.05)

        self.spin_soc_max = QDoubleSpinBox()
        self.spin_soc_max.setRange(0.0, 1.0)
        self.spin_soc_max.setDecimals(2)
        self.spin_soc_max.setSingleStep(0.05)

        self.spin_soc_target = QDoubleSpinBox()
        self.spin_soc_target.setRange(0.1, 1.0)
        self.spin_soc_target.setDecimals(2)
        self.spin_soc_target.setSingleStep(0.05)

        self.spin_wait = QSpinBox()
        self.spin_wait.setRange(5, 240)
        self.spin_wait.setSuffix(" min")

        self.spin_seed = QSpinBox()
        self.spin_seed.setRange(1, 999999)

        form_pojazdy.addRow("Liczba sesji bazowych / doba:", self.spin_liczba_sesji)
        form_pojazdy.addRow("Miks pojazdów:", self.combo_miks)
        form_pojazdy.addRow("SOC początkowy min:", self.spin_soc_min)
        form_pojazdy.addRow("SOC początkowy max:", self.spin_soc_max)
        form_pojazdy.addRow("SOC docelowy:", self.spin_soc_target)
        form_pojazdy.addRow("Maks. czas oczekiwania:", self.spin_wait)
        form_pojazdy.addRow("Ziarno losowe:", self.spin_seed)

        grupa_scenariusze = QGroupBox("Scenariusze")
        uklad_sc = QVBoxLayout(grupa_scenariusze)
        self.checkbox_scenariusze = {}
        for identyfikator, scenariusz in self.scenariusze.items():
            checkbox = QCheckBox(scenariusz.nazwa)
            self.checkbox_scenariusze[identyfikator] = checkbox
            uklad_sc.addWidget(checkbox)

        grupa_przyciski = QGroupBox("Sterowanie")
        uklad_przyciski = QVBoxLayout(grupa_przyciski)
        self.btn_uruchom = QPushButton("Uruchom zaznaczone scenariusze")
        self.btn_uruchom_all = QPushButton("Uruchom wszystkie 4 scenariusze")
        self.btn_eksport = QPushButton("Eksportuj ostatnie wyniki")
        self.btn_eksport.setEnabled(False)
        self.btn_uruchom.clicked.connect(self._uruchom_zaznaczone)
        self.btn_uruchom_all.clicked.connect(self._uruchom_wszystkie)
        self.btn_eksport.clicked.connect(self._eksportuj)
        uklad_przyciski.addWidget(self.btn_uruchom)
        uklad_przyciski.addWidget(self.btn_uruchom_all)
        uklad_przyciski.addWidget(self.btn_eksport)

        opis = QLabel(
            "Aplikacja działa offline. Wczytuje lokalne CSV oparte na realnych źródłach "
            "i generuje syntetyczne profile obciążenia dla stacji EV."
        )
        opis.setWordWrap(True)

        uklad.addWidget(grupa_stacja)
        uklad.addWidget(grupa_pojazdy)
        uklad.addWidget(grupa_scenariusze)
        uklad.addWidget(grupa_przyciski)
        uklad.addWidget(opis)
        uklad.addStretch(1)
        kontener.setMaximumWidth(420)
        return kontener

    def _zbuduj_panel_wynikow(self) -> QWidget:
        kontener = QWidget()
        uklad = QVBoxLayout(kontener)

        self.tabs = QTabWidget()
        uklad.addWidget(self.tabs)

        zakladka_podsumowanie = QWidget()
        uklad_podsumowanie = QVBoxLayout(zakladka_podsumowanie)
        self.combo_podglad_scenariusza = QComboBox()
        self.combo_podglad_scenariusza.currentTextChanged.connect(self._odswiez_widoki_po_wyborze)
        uklad_podsumowanie.addWidget(QLabel("Podgląd wyników scenariusza:"))
        uklad_podsumowanie.addWidget(self.combo_podglad_scenariusza)

        self.tabela_podsumowanie = QTableWidget()
        self.tabela_podsumowanie.setColumnCount(2)
        self.tabela_podsumowanie.setHorizontalHeaderLabels(["Miara", "Wartość"])
        uklad_podsumowanie.addWidget(self.tabela_podsumowanie)

        self.pole_opisu = QTextEdit()
        self.pole_opisu.setReadOnly(True)
        uklad_podsumowanie.addWidget(self.pole_opisu)
        self.tabs.addTab(zakladka_podsumowanie, "Wyniki liczbowe")

        zakladka_wykresy = QWidget()
        uklad_wykresy = QVBoxLayout(zakladka_wykresy)

        pasek_wykresow = QHBoxLayout()
        self.combo_wykres = QComboBox()
        for klucz, nazwa in self.mapowanie_wykresow.items():
            self.combo_wykres.addItem(nazwa, klucz)
        self.combo_wykres.currentIndexChanged.connect(self._odswiez_wykres)

        self.btn_zapisz_wykres = QPushButton("Zapisz aktualny wykres do PNG")
        self.btn_zapisz_wykres.setEnabled(False)
        self.btn_zapisz_wykres.clicked.connect(self._zapisz_wykres_png)

        pasek_wykresow.addWidget(QLabel("Wybierz wykres:"))
        pasek_wykresow.addWidget(self.combo_wykres, 1)
        pasek_wykresow.addWidget(self.btn_zapisz_wykres)

        self.etykieta_opisu_wykresu = QLabel(
            "Po uruchomieniu symulacji wybierz z listy wykres, który chcesz obejrzeć."
        )
        self.etykieta_opisu_wykresu.setWordWrap(True)

        self.canvas_wykres = PlatnoWykresu()

        uklad_wykresy.addLayout(pasek_wykresow)
        uklad_wykresy.addWidget(self.etykieta_opisu_wykresu)
        uklad_wykresy.addWidget(self.canvas_wykres, 1)
        self.tabs.addTab(zakladka_wykresy, "Wykresy")

        zakladka_tabele = QWidget()
        uklad_tabele = QVBoxLayout(zakladka_tabele)
        self.tabs_tabele = QTabWidget()
        self.tabela_profil = QTableWidget()
        self.tabela_sesje = QTableWidget()
        self.tabela_zdarzenia = QTableWidget()
        self.tabela_stat = QTableWidget()
        self.tabs_tabele.addTab(self.tabela_profil, "Profil czasowy")
        self.tabs_tabele.addTab(self.tabela_sesje, "Sesje")
        self.tabs_tabele.addTab(self.tabela_zdarzenia, "Zdarzenia")
        self.tabs_tabele.addTab(self.tabela_stat, "Analiza statystyczna")
        uklad_tabele.addWidget(self.tabs_tabele)
        self.tabs.addTab(zakladka_tabele, "Tabele")

        zakladka_zrodla = QWidget()
        uklad_zrodla = QVBoxLayout(zakladka_zrodla)
        self.pole_zrodla = QTextEdit()
        self.pole_zrodla.setReadOnly(True)
        uklad_zrodla.addWidget(self.pole_zrodla)
        self.tabs.addTab(zakladka_zrodla, "Źródła danych / opis danych")
        return kontener

    def _wczytaj_domyslne_wartosci(self) -> None:
        stacja = self.ustawienia["domyslne_parametry_stacji"]
        pojazdy = self.ustawienia["domyslne_parametry_pojazdow"]

        self.spin_ladowarki.setValue(stacja["liczba_ladowarek"])
        self.combo_typ.setCurrentText(stacja["typ_ladowarki"])
        self.spin_moc_ladowarki.setValue(stacja["moc_ladowarki_kw"])
        self.spin_limit_mocy.setValue(stacja["limit_mocy_stacji_kw"])
        self.spin_sprawnosc.setValue(stacja["sprawnosc"])
        self.spin_napiecie.setValue(stacja["napiecie_v"])

        self.spin_liczba_sesji.setValue(pojazdy["liczba_sesji"])
        self.combo_miks.setCurrentText(pojazdy["miks_pojazdow"])
        self.spin_soc_min.setValue(pojazdy["soc_poczatkowy_min"])
        self.spin_soc_max.setValue(pojazdy["soc_poczatkowy_max"])
        self.spin_soc_target.setValue(pojazdy["soc_docelowy"])
        self.spin_wait.setValue(pojazdy["maks_czas_oczekiwania_min"])
        self.spin_seed.setValue(pojazdy["ziarno"])

        for identyfikator in self.ustawienia["domyslne_scenariusze"]:
            if identyfikator in self.checkbox_scenariusze:
                self.checkbox_scenariusze[identyfikator].setChecked(True)

    def _odswiez_tekst_zrodel(self) -> None:
        pelny_opis = self.opis_danych_md + "\n\n---\n\n" + opis_funkcji_pradu_markdown()
        self.pole_zrodla.setMarkdown(pelny_opis)

    def _zbierz_parametry(self) -> tuple[ParametryStacji, ParametryGeneracjiPojazdow]:
        if self.spin_soc_min.value() >= self.spin_soc_max.value():
            raise ValueError("SOC początkowy min musi być mniejszy od SOC początkowy max.")
        if self.spin_soc_target.value() <= self.spin_soc_min.value():
            raise ValueError("SOC docelowy powinien być większy od minimalnego SOC początkowego.")

        param_stacja = ParametryStacji(
            liczba_ladowarek=self.spin_ladowarki.value(),
            typ_ladowarki=self.combo_typ.currentText(),
            moc_ladowarki_kw=self.spin_moc_ladowarki.value(),
            limit_mocy_stacji_kw=self.spin_limit_mocy.value(),
            sprawnosc=self.spin_sprawnosc.value(),
            napiecie_v=self.spin_napiecie.value(),
        )
        param_pojazdy = ParametryGeneracjiPojazdow(
            liczba_sesji=self.spin_liczba_sesji.value(),
            miks_pojazdow=self.combo_miks.currentText(),
            soc_poczatkowy_min=self.spin_soc_min.value(),
            soc_poczatkowy_max=self.spin_soc_max.value(),
            soc_docelowy=self.spin_soc_target.value(),
            maks_czas_oczekiwania_min=self.spin_wait.value(),
            ziarno=self.spin_seed.value(),
        )
        return param_stacja, param_pojazdy

    def _zaznaczone_scenariusze(self) -> list[str]:
        return [ident for ident, cb in self.checkbox_scenariusze.items() if cb.isChecked()]

    def _pobierz_aktualny_wynik(self):
        ident = self.combo_podglad_scenariusza.currentData()
        if ident is None or ident not in self.ostatnie_wyniki:
            return None
        return self.ostatnie_wyniki[ident]

    def _uruchom_zaznaczone(self) -> None:
        zaznaczone = self._zaznaczone_scenariusze()
        if not zaznaczone:
            QMessageBox.warning(self, "Brak scenariusza", "Zaznacz przynajmniej jeden scenariusz.")
            return
        self._uruchom_scenariusze(zaznaczone)

    def _uruchom_wszystkie(self) -> None:
        self._uruchom_scenariusze(list(self.scenariusze.keys()))

    def _uruchom_scenariusze(self, identyfikatory: list[str]) -> None:
        try:
            param_stacja, param_pojazdy = self._zbierz_parametry()
            wyniki = {}
            for ident in identyfikatory:
                wynik = self.symulator.uruchom(
                    parametry_stacji=param_stacja,
                    parametry_pojazdow=param_pojazdy,
                    scenariusz=self.scenariusze[ident],
                    pojazdy_df=self.pojazdy_df,
                )
                wyniki[ident] = wynik
            self.ostatnie_wyniki = wyniki
            self.btn_eksport.setEnabled(True)
            self.btn_zapisz_wykres.setEnabled(True)
            self._zaladuj_wyniki_do_gui()
            QMessageBox.information(
                self,
                "Symulacja zakończona",
                f"Zakończono symulację dla {len(wyniki)} scenariuszy.",
            )
        except Exception as exc:
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas symulacji:\n{exc}")

    def _zaladuj_wyniki_do_gui(self) -> None:
        self.combo_podglad_scenariusza.blockSignals(True)
        self.combo_podglad_scenariusza.clear()
        for ident, wynik in self.ostatnie_wyniki.items():
            self.combo_podglad_scenariusza.addItem(wynik.scenariusz.nazwa, ident)
        self.combo_podglad_scenariusza.blockSignals(False)
        self._odswiez_widoki_po_wyborze()

    def _odswiez_widoki_po_wyborze(self) -> None:
        wynik = self._pobierz_aktualny_wynik()
        if wynik is None:
            return

        self._wypelnij_tabele_podsumowania(wynik.podsumowanie)
        self._wypelnij_tabele_z_df(self.tabela_profil, wynik.profil_czasowy)
        self._wypelnij_tabele_z_df(self.tabela_sesje, wynik.sesje)
        self._wypelnij_tabele_z_df(self.tabela_zdarzenia, wynik.zdarzenia)
        self._wypelnij_tabele_z_df(self.tabela_stat, wynik.analiza_statystyczna)

        self._odswiez_wykres()

        tekst = self._zbuduj_opis_wynikow()
        self.pole_opisu.setMarkdown(tekst)

    def _odswiez_wykres(self) -> None:
        wynik = self._pobierz_aktualny_wynik()
        if wynik is None:
            return

        typ_wykresu = self.combo_wykres.currentData()
        if typ_wykresu == "profil_mocy":
            self.menedzer_wykresow.rysuj_moc(self.canvas_wykres, wynik.profil_czasowy)
            opis = "Pokazuje chwilową moc całej stacji w kolejnych krokach czasu."
        elif typ_wykresu == "profil_pradu":
            self.menedzer_wykresow.rysuj_prad(self.canvas_wykres, wynik.profil_czasowy)
            opis = "Pokazuje łączny prąd pobierany przez stację w czasie."
        elif typ_wykresu == "zajetosc_ladowarek":
            self.menedzer_wykresow.rysuj_zajetosc(self.canvas_wykres, wynik.profil_czasowy)
            opis = "Pokazuje liczbę aktywnie zajętych ładowarek w kolejnych chwilach."
        elif typ_wykresu == "kolejka":
            self.menedzer_wykresow.rysuj_kolejke(self.canvas_wykres, wynik.profil_czasowy)
            opis = "Pokazuje ilu kierowców czekało na wolną ładowarkę."
        else:
            self.menedzer_wykresow.rysuj_histogram(self.canvas_wykres, wynik.sesje)
            opis = "Pokazuje rozkład długości sesji ładowania dla wybranego scenariusza."

        self.etykieta_opisu_wykresu.setText(opis)

    def _zbuduj_opis_wynikow(self) -> str:
        if not self.ostatnie_wyniki:
            return "Brak wyników."

        linie = ["## Zbiorcza interpretacja wyników", ""]
        for wynik in self.ostatnie_wyniki.values():
            p = wynik.podsumowanie
            linie.extend(
                [
                    f"### {p['scenariusz']}",
                    f"- sesje wygenerowane: **{p['liczba_sesji_wygenerowanych']}**",
                    f"- sesje zakończone: **{p['sesje_zakonczone']}**",
                    f"- rezygnacje: **{p['sesje_rezygnacja']}**",
                    f"- moc szczytowa: **{p['moc_szczytowa_kw']} kW**",
                    f"- średni czas oczekiwania: **{p['sredni_czas_oczekiwania_min']} min**",
                    f"- energia całkowita: **{p['energia_calkowita_kwh']} kWh**",
                    "",
                ]
            )
        return "\n".join(linie)

    def _wypelnij_tabele_podsumowania(self, podsumowanie: dict) -> None:
        self.tabela_podsumowanie.setRowCount(len(podsumowanie))
        for wiersz, (klucz, wartosc) in enumerate(podsumowanie.items()):
            self.tabela_podsumowanie.setItem(wiersz, 0, QTableWidgetItem(str(klucz)))
            self.tabela_podsumowanie.setItem(wiersz, 1, QTableWidgetItem(str(wartosc)))
        self.tabela_podsumowanie.resizeColumnsToContents()

    def _wypelnij_tabele_z_df(self, tabela: QTableWidget, df: pd.DataFrame) -> None:
        tabela.setColumnCount(len(df.columns))
        tabela.setHorizontalHeaderLabels([str(c) for c in df.columns])
        tabela.setRowCount(len(df.index))
        for i, (_, wiersz) in enumerate(df.iterrows()):
            for j, kol in enumerate(df.columns):
                tabela.setItem(i, j, QTableWidgetItem(str(wiersz[kol])))
        tabela.resizeColumnsToContents()

    def _zapisz_wykres_png(self) -> None:
        wynik = self._pobierz_aktualny_wynik()
        if wynik is None:
            QMessageBox.warning(self, "Brak danych", "Najpierw uruchom symulację i wybierz scenariusz.")
            return

        nazwa_scenariusza = wynik.scenariusz.identyfikator
        nazwa_wykresu = self.combo_wykres.currentData() or "wykres"
        proponowana = f"{nazwa_scenariusza}_{nazwa_wykresu}.png"
        startowy_katalog = str(self.katalog_projektu / "exports")

        sciezka, _ = QFileDialog.getSaveFileName(
            self,
            "Zapisz wykres do pliku PNG",
            str(Path(startowy_katalog) / proponowana),
            "Pliki PNG (*.png)",
        )
        if not sciezka:
            return

        try:
            self.canvas_wykres.figure.savefig(sciezka, dpi=150, bbox_inches="tight")
            QMessageBox.information(self, "Zapisano", f"Wykres zapisano do pliku:\n{sciezka}")
        except Exception as exc:
            QMessageBox.critical(self, "Błąd zapisu", f"Nie udało się zapisać wykresu:\n{exc}")

    def _eksportuj(self) -> None:
        if not self.ostatnie_wyniki:
            QMessageBox.warning(self, "Brak wyników", "Najpierw uruchom symulację.")
            return
        try:
            katalog = self.eksporter.eksportuj(self.ostatnie_wyniki, nazwa_prefix="eksport_gui")
            QMessageBox.information(
                self,
                "Eksport zakończony",
                f"Wyniki zapisano w katalogu:\n{katalog}",
            )
        except Exception as exc:
            QMessageBox.critical(self, "Błąd eksportu", f"Nie udało się zapisać eksportu:\n{exc}")
