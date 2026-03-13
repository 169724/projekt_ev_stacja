# Opis danych CSV

Ten dokument opisuje wszystkie pliki CSV użyte w projekcie.

---

## 1. `data/raw/typy_ladowarek_zrodla.csv`

**Cel pliku:**  
Surowy opis typów ładowarek i mocy referencyjnych.

**Rodzaj danych:** surowe

**Kolumny:**
- `typ_id` – identyfikator techniczny,
- `nazwa` – czytelna nazwa typu ładowarki,
- `rodzaj_pradu` – AC albo DC,
- `napiecie_zrodlo_v` – napięcie lub zakres napięcia ze źródła,
- `moc_min_kw` – minimalna moc referencyjna [kW],
- `moc_typowa_kw` – typowa moc [kW],
- `moc_max_kw` – moc maksymalna [kW],
- `opis` – krótki opis użycia,
- `zrodlo_nazwa` – nazwa źródła,
- `zrodlo_url` – adres źródła,
- `status_danych` – informacja, że to dane surowe.

**Jednostki:** kW, V

**Do czego służy w programie?**  
Do dokumentacji i opisu źródeł danych.

---

## 2. `data/raw/pojazdy_ev_zrodla.csv`

**Cel pliku:**  
Surowe parametry pojazdów EV z oficjalnych stron producentów.

**Rodzaj danych:** surowe

**Kolumny:**
- `pojazd_id` – identyfikator pojazdu,
- `nazwa_pojazdu` – nazwa modelu,
- `segment` – uproszczony segment pojazdu,
- `pojemnosc_baterii_kwh` – pojemność baterii [kWh],
- `czas_ac_0_100_h` – czas ładowania AC 0–100% [h],
- `czas_dc_10_80_min` – czas ładowania DC 10–80% [min],
- `moc_stacji_referencyjnej_dc_kw` – moc stacji referencyjnej użytej w źródle [kW],
- `oficjalna_moc_ac_kw` – maksymalna moc AC pojazdu [kW], jeśli podana,
- `oficjalna_moc_dc_kw` – maksymalna moc DC pojazdu [kW], jeśli podana,
- `uwagi` – komentarz metodologiczny,
- `zrodlo_nazwa` – nazwa źródła,
- `zrodlo_url` – adres źródła,
- `status_danych` – informacja, że to dane surowe.

**Jednostki:** kWh, h, min, kW

**Do czego służy w programie?**  
Jest wejściem dla skryptu `app/data_processing/prepare_data.py`.

---

## 3. `data/raw/zrodla_scenariuszy.csv`

**Cel pliku:**  
Zebrane notatki źródłowe dotyczące scenariuszy ruchu, temperatury i taperingu.

**Rodzaj danych:** surowe

**Kolumny:**
- `obszar` – obszar tematyczny,
- `wartosc` – skrócona wartość lub hasło,
- `opis` – interpretacja źródła,
- `zrodlo_nazwa` – źródło,
- `zrodlo_url` – adres,
- `status_danych` – informacja, że to dane surowe.

**Do czego służy w programie?**  
Do dokumentacji i weryfikacji sposobu budowy scenariuszy.

---

## 4. `data/processed/pojazdy_domyslne.csv`

**Cel pliku:**  
Przetworzone parametry pojazdów gotowe do użycia w symulacji.

**Rodzaj danych:** przetworzone

**Kolumny:**
- `pojazd_id` – identyfikator,
- `nazwa_pojazdu` – nazwa modelu,
- `segment` – segment,
- `pojemnosc_baterii_kwh` – pojemność baterii [kWh],
- `ac_max_kw` – maksymalna moc AC [kW],
- `dc_max_kw` – maksymalna moc DC [kW],
- `udzial_w_miksie` – udział w losowaniu floty,
- `zrodlo_nazwa` – źródło,
- `zrodlo_url` – adres źródła,
- `status_danych` – status,
- `uwaga_przetworzenie` – jak wyznaczono wartości.

**Jednostki:** kWh, kW

**Do czego służy w programie?**  
To główny plik wejściowy dla generatora pojazdów.

---

## 5. `data/processed/profile_scenariuszy_godzinowe.csv`

**Cel pliku:**  
Godzinowe profile przyjazdów dla 4 scenariuszy symulacyjnych.

**Rodzaj danych:** przetworzone

**Kolumny:**
- `scenariusz` – identyfikator scenariusza,
- `nazwa` – nazwa scenariusza,
- `pora_roku` – lato / zima,
- `typ_dnia` – dzień roboczy / weekend,
- `godzina` – godzina 0–23,
- `waga_przyjazdu` – znormalizowana waga przyjazdu,
- `wspolczynnik_naplywu` – mnożnik liczby sesji,
- `wspolczynnik_temperatury_mocy` – mnożnik mocy ładowania,
- `wspolczynnik_energii` – mnożnik energii na sesję,
- `opis` – opis scenariusza,
- `metoda` – opis metody utworzenia.

**Jednostki:** bezwymiarowe, godziny

**Do czego służy w programie?**  
Plik zasila generator przyjazdów i wpływa na przebieg symulacji.

---

## 6. Pliki eksportowe w `exports/...`

**Cel plików:**  
Wyniki każdej symulacji.

**Rodzaj danych:** wynikowe

**Przykładowe pliki:**
- `profil_czasowy.csv` – moc, prąd, aktywne sesje, kolejka w czasie,
- `sesje.csv` – tabela pojedynczych sesji,
- `zdarzenia.csv` – dziennik zdarzeń,
- `analiza_statystyczna.csv` – statystyki opisowe,
- `podsumowanie_scenariuszy.csv` – zbiorcza tabela scenariuszy.

**Do czego służą w programie?**  
Do raportowania, oddania projektu i dalszej analizy.
