# Symulator stacji ładowania EV

Kompletny projekt desktopowy w Pythonie, który:
- symuluje pracę stacji ładowania EV w czasie,
- pozwala parametryzować stację i generator pojazdów,
- obsługuje 4 scenariusze symulacyjne,
- generuje syntetyczne profile obciążenia,
- pokazuje wykresy i tabele bezpośrednio w GUI,
- eksportuje wyniki do CSV, JSON i Markdown.

Projekt został przygotowany tak, aby można go było uruchomić lokalnie w **PyCharm**.

---

## 1. Zakres projektu

Program realizuje temat:

**„Algorytm symulujący pracę stacji ładowania EV: model ma odtwarzać zachowanie ładowarek w czasie, być parametryzowalny, generować syntetyczne profile obciążenia, eksportować wyniki i zawierać funkcję opisującą wartość prądu ładowania w różnych scenariuszach. Program ma obejmować pełny kod, raportowe dane wyjściowe, minimum 4 scenariusze symulacyjne, wykresy i analizę statystyczną wyników.”**

---

## 2. Główne funkcje programu

### GUI
Aplikacja ma interfejs w PySide6 i zawiera:
- formularz parametrów wejściowych,
- wybór scenariuszy,
- przyciski uruchamiania symulacji,
- sekcję wyników liczbowych,
- wykresy osadzone w GUI,
- wybór pojedynczego wykresu z listy rozwijanej,
- zapis aktualnie oglądanego wykresu do pliku PNG,
- podgląd danych tabelarycznych,
- zakładkę „Źródła danych / opis danych”,
- możliwość eksportu wyników.

### Logika symulacji
Model obejmuje:
- przyjazd pojazdu,
- oczekiwanie w kolejce,
- rozpoczęcie ładowania,
- zmianę mocy ładowania w czasie,
- zakończenie sesji,
- rezygnację po przekroczeniu czasu oczekiwania,
- ograniczenie mocy całej stacji,
- rozdział mocy między aktywne sesje.

### Wyniki
Program oblicza i pokazuje:
- profil mocy,
- profil prądu,
- liczbę aktywnych sesji,
- długość kolejki,
- energię na sesję,
- czas ładowania,
- czas oczekiwania,
- moc szczytową,
- analizę statystyczną wyników.

---

## 3. Architektura techniczna

### Zastosowane biblioteki
- **Python 3.11+** – stabilna wersja wygodna do uruchamiania w PyCharm,
- **PySide6** – nowoczesne GUI desktopowe,
- **matplotlib** – wykresy osadzone w oknie aplikacji,
- **pandas** – tabele, CSV i przygotowanie danych,
- **numpy** – losowanie i obliczenia numeryczne,
- **pytest** – podstawowe testy.

### Dlaczego taki stos?
- jest prosty i czytelny,
- dobrze nadaje się do projektu studenckiego,
- działa lokalnie,
- nie wymaga serwera ani bazy danych.

---

## 4. Struktura folderów

```text
projekt_ev_stacja/
├── app/
│   ├── charts/
│   │   └── plot_manager.py
│   ├── core/
│   │   ├── current_power.py
│   │   └── simulation.py
│   ├── data_processing/
│   │   ├── data_loader.py
│   │   └── prepare_data.py
│   ├── exporters/
│   │   └── exporter.py
│   ├── gui/
│   │   └── main_window.py
│   └── models.py
├── config/
│   └── settings.json
├── data/
│   ├── raw/
│   │   ├── pojazdy_ev_zrodla.csv
│   │   ├── typy_ladowarek_zrodla.csv
│   │   └── zrodla_scenariuszy.csv
│   └── processed/
│       ├── pojazdy_domyslne.csv
│       └── profile_scenariuszy_godzinowe.csv
├── docs/
│   ├── opis_danych.md
│   └── zrodla_danych.md
├── exports/
│   └── .gitkeep
├── tests/
│   ├── test_calculations.py
│   ├── test_export.py
│   └── test_simulation.py
├── .gitignore
├── main.py
└── requirements.txt
```

---

## 5. Scenariusze symulacyjne

W projekcie są 4 scenariusze:
1. **Lato – dzień roboczy**
2. **Lato – weekend**
3. **Zima – dzień roboczy**
4. **Zima – weekend**

### Jak zostały zbudowane?
Scenariusze są **syntetyczne**, ale oparte na realnych źródłach:
- opisach godzinowych pików ruchu drogowego,
- wpływie temperatury na szybkość ładowania,
- zjawisku taperingu po 80% SOC,
- danych producentów dotyczących pojazdów,
- typowych parametrach ładowarek z DOE/AFDC.

Szczegóły opisano w:
- `docs/zrodla_danych.md`
- `docs/opis_danych.md`

---

## 6. Funkcja prądu ładowania

W projekcie zaimplementowano funkcję opisującą prąd:

### AC
\[
I_{AC} = \frac{P}{\sqrt{3} \cdot U \cdot cos\varphi}
\]

### DC
\[
I_{DC} = \frac{P}{U}
\]

Dla DC zastosowano uproszczone ograniczanie mocy wraz ze wzrostem SOC.
W scenariuszach zimowych dodatkowo używany jest współczynnik temperaturowy.

Implementacja:
- `app/core/current_power.py`

---

## 7. Dane źródłowe i metodologia

### Ważna uwaga metodologiczna
Projekt nie zakłada, że mamy pełny pomiar z jednej, konkretnej stacji EV.
Zamiast tego:
1. zebrano **realne dane źródłowe**,
2. zapisano je w `data/raw/`,
3. przygotowano dane **przetworzone** w `data/processed/`,
4. na ich podstawie symulator generuje profile syntetyczne.

To podejście jest uczciwe, praktyczne i łatwe do obrony:
- źródła są prawdziwe,
- założenia są jawne,
- dane przetworzone są opisane.

---

## 8. Opis plików CSV

Szczegółowy opis wszystkich CSV znajduje się w:
- `docs/opis_danych.md`

Najważniejsze pliki:
- `data/raw/pojazdy_ev_zrodla.csv` – surowe parametry aut,
- `data/raw/typy_ladowarek_zrodla.csv` – surowe typy ładowarek,
- `data/raw/zrodla_scenariuszy.csv` – źródła do budowy scenariuszy,
- `data/processed/pojazdy_domyslne.csv` – dane wejściowe do symulacji,
- `data/processed/profile_scenariuszy_godzinowe.csv` – scenariusze godzinowe,
- `exports/...` – dane wynikowe wygenerowane przez aplikację.

---

## 9. Instrukcja uruchomienia w PyCharm

### Krok 1
Otwórz folder projektu w PyCharm.

### Krok 2
Utwórz interpreter z Pythonem 3.11 lub nowszym.

### Krok 3
Zainstaluj zależności:

```bash
pip install -r requirements.txt
```

### Krok 4
Uruchom plik:

```bash
main.py
```

### Krok 5
W GUI:
- ustaw parametry stacji,
- wybierz scenariusze,
- kliknij uruchomienie,
- obejrzyj wykresy i tabele,
- wyeksportuj wyniki.

---

## 10. Uruchomienie testów

W terminalu projektu:

```bash
pytest
```

Zakres testów:
- poprawność obliczania prądu,
- poprawność ograniczeń mocy,
- poprawność działania symulacji,
- poprawność eksportu.

---

## 11. Logika działania programu

Uproszczony przepływ:

1. wczytanie danych przetworzonych,
2. wybór scenariusza,
3. wygenerowanie sesji pojazdów,
4. przejście po kolejnych krokach czasu,
5. obsługa przyjazdów i kolejki,
6. przydział ładowarek,
7. obliczenie chwilowej mocy i prądu,
8. aktualizacja SOC i energii,
9. zamknięcie sesji lub rezygnacja,
10. zapis wyników do tabel, wykresów i eksportu.

---

## 12. Co znajduje się w wynikach eksportu?

Po eksporcie program tworzy katalog z:
- `podsumowanie_scenariuszy.csv`,
- `wejscie.json`,
- `raport.md`,
- osobnym podfolderem dla każdego scenariusza:
  - `profil_czasowy.csv`,
  - `sesje.csv`,
  - `zdarzenia.csv`,
  - `analiza_statystyczna.csv`.

---

## 13. Możliwe rozszerzenia

Projekt można dalej rozbudować o:
- taryfy energii i koszty,
- magazyn energii,
- fotowoltaikę,
- rezerwacje ładowarek,
- różne polityki kolejkowania,
- dokładniejsze krzywe ładowania dla konkretnych modeli aut,
- import danych z API operatorów stacji.

---

## 14. Uwagi końcowe

Projekt jest przygotowany jako:
- prosty,
- modularny,
- czytelny,
- spolszczony,
- gotowy do uruchomienia lokalnie,
- nadający się do oddania i omówienia na studiach.
