"""Obsługa wykresów osadzonych w GUI."""

from __future__ import annotations

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure


class PlatnoWykresu(FigureCanvasQTAgg):
    """Proste płótno matplotlib do osadzania w PySide6."""

    def __init__(self, szerokosc: float = 9.5, wysokosc: float = 4.8, dpi: int = 100) -> None:
        self.figure = Figure(figsize=(szerokosc, wysokosc), dpi=dpi, tight_layout=True)
        self.axes = self.figure.add_subplot(111)
        super().__init__(self.figure)


class MenedzerWykresow:
    """Zbiór metod rysujących wyniki symulacji."""

    @staticmethod
    def _ustaw_czas_na_osi(ax, etykiety_czasu: list[str]) -> None:
        """Ustawia czytelną oś czasu bez nakładania wszystkich opisów."""
        if not etykiety_czasu:
            return

        krok = max(1, len(etykiety_czasu) // 12)
        pozycje = list(range(0, len(etykiety_czasu), krok))
        if pozycje[-1] != len(etykiety_czasu) - 1:
            pozycje.append(len(etykiety_czasu) - 1)

        ax.set_xticks(pozycje)
        ax.set_xticklabels([etykiety_czasu[i] for i in pozycje], rotation=35, ha="right")

    def _stylizuj_os(self, ax, tytul: str, etykieta_y: str, etykiety_czasu: list[str] | None = None) -> None:
        ax.set_title(tytul)
        ax.set_xlabel("Czas")
        ax.set_ylabel(etykieta_y)
        ax.grid(True, alpha=0.3)
        if etykiety_czasu is not None:
            self._ustaw_czas_na_osi(ax, etykiety_czasu)

    def rysuj_moc(self, canvas: PlatnoWykresu, profil_df) -> None:
        ax = canvas.axes
        ax.clear()
        x = list(range(len(profil_df)))
        etykiety = profil_df["czas"].astype(str).tolist()
        ax.plot(x, profil_df["moc_calkowita_kw"], marker="o", markersize=2.5, linewidth=1.4)
        self._stylizuj_os(ax, "Profil mocy w czasie", "Moc [kW]", etykiety)
        canvas.draw_idle()

    def rysuj_prad(self, canvas: PlatnoWykresu, profil_df) -> None:
        ax = canvas.axes
        ax.clear()
        x = list(range(len(profil_df)))
        etykiety = profil_df["czas"].astype(str).tolist()
        ax.plot(x, profil_df["prad_calkowity_a"], marker="o", markersize=2.5, linewidth=1.4)
        self._stylizuj_os(ax, "Profil prądu w czasie", "Prąd [A]", etykiety)
        canvas.draw_idle()

    def rysuj_zajetosc(self, canvas: PlatnoWykresu, profil_df) -> None:
        ax = canvas.axes
        ax.clear()
        x = list(range(len(profil_df)))
        etykiety = profil_df["czas"].astype(str).tolist()
        ax.step(x, profil_df["aktywne_sesje"], where="mid")
        self._stylizuj_os(ax, "Liczba zajętych ładowarek", "Aktywne sesje", etykiety)
        canvas.draw_idle()

    def rysuj_kolejke(self, canvas: PlatnoWykresu, profil_df) -> None:
        ax = canvas.axes
        ax.clear()
        x = list(range(len(profil_df)))
        etykiety = profil_df["czas"].astype(str).tolist()
        ax.step(x, profil_df["kolejka"], where="mid")
        self._stylizuj_os(ax, "Długość kolejki", "Pojazdy w kolejce", etykiety)
        canvas.draw_idle()

    def rysuj_histogram(self, canvas: PlatnoWykresu, sesje_df) -> None:
        ax = canvas.axes
        ax.clear()
        dane = sesje_df["czas_ladowania_min"].fillna(0.0)
        ax.hist(dane, bins=12)
        ax.set_title("Histogram czasu ładowania")
        ax.set_xlabel("Czas ładowania [min]")
        ax.set_ylabel("Liczba sesji")
        ax.grid(True, alpha=0.3)
        canvas.draw_idle()
