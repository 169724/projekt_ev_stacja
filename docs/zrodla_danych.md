# Źródła danych

Projekt korzysta z **lokalnych plików CSV**, ale ich wartości bazowe pochodzą z realnych, publicznie dostępnych źródeł.
Program po uruchomieniu **nie pobiera danych z internetu**, dzięki czemu działa lokalnie i stabilnie w PyCharm.

## 1. Parametry ładowarek

### Źródła:
1. **U.S. Department of Energy (FEMP)** – typowe moce EVSE AC Level 2, DCFC i XFC.
2. **Alternative Fuels Data Center (DOE AFDC)** – opis DC fast charging do 500 kW.
3. **U.S. Department of Transportation** – opisy poziomów ładowania i napięć.

### Zastosowanie w projekcie:
- dobór domyślnych typów ładowarek AC/DC,
- zakresy mocy w GUI,
- opis źródeł danych.

## 2. Parametry pojazdów

### Źródła:
1. **BMW** – oficjalna tabela techniczna BMW i4 eDrive40.
2. **Nissan USA** – oficjalna strona LEAF.
3. **Hyundai Europe / Hyundai Global** – IONIQ 5, pojemność baterii i czasy ładowania.
4. **Volvo Support** – EX30, czasy ładowania AC/DC i pojemność baterii.

### Zastosowanie w projekcie:
- zbudowanie pliku `data/raw/pojazdy_ev_zrodla.csv`,
- utworzenie pliku przetworzonego `data/processed/pojazdy_domyslne.csv`,
- losowanie floty pojazdów podczas symulacji.

## 3. Scenariusze ruchu i sezonowości

### Źródła:
1. **Department for Transport (UK)** – opis godzinowych pików ruchu samochodów:
   - dzień roboczy: pik popołudniowy,
   - weekend: pik w środku dnia.
2. **U.S. EPA** – wpływ temperatury na ładowanie i zjawisko spadku mocy po około 80% SOC.
3. **NREL** – założenie 90% sprawności AC w modelu infrastrukturalnym.
4. **Publikacja naukowa PW** – opis wpływu sezonowości i typu dnia na natężenie ruchu.

### Jak z tych danych powstały scenariusze?
W projekcie **nie udajemy, że mamy pełny pomiar z jednej rzeczywistej stacji EV**.  
Zamiast tego użyto metody:
- realne źródła → opis zachowania ruchu i ładowania,
- na ich podstawie → syntetyczne profile godzinowe,
- profile zapisano do `data/processed/profile_scenariuszy_godzinowe.csv`.

Dzięki temu projekt jest uczciwy metodologicznie:
- dane źródłowe są realne,
- dane scenariuszowe są **przetworzone / syntetyczne**,
- założenia są jawne i opisane.

## 4. Dlaczego aplikacja działa offline?

Celowo przyjęto model:
- **źródła realne i opisane**,
- **dane lokalne**,
- **brak zależności od internetu podczas uruchamiania**.

To upraszcza:
- uruchomienie w PyCharm,
- obronę projektu,
- powtarzalność wyników.
