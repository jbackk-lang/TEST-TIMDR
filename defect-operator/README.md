# Kandydat na operator defektu v2 — entropia permutacyjna + dryf względem referencji

## STATUS: FALSYFIKACJA v1 — punkt wyjścia do wersji adaptacyjnej

Ten dokument jest formalnie zapisany jako **falsyfikacja pierwszego
podejścia** (entropia permutacyjna + jedna stała referencja), nie jako
porażka projektu jako całości. Wynik testu (patrz "Wyniki"/"Werdykt"
niżej) obala v1 w dwóch konkretnych, zmierzonych punktach (R1/R2 nie
generalizuje na zmianę tła; R3 nie pokazuje przewagi nad CV dla
defektu okresowego) i **jednoznacznie wskazuje trzy kierunki dla v2**,
zdefiniowane wprost jako następny krok, nie jako luźna sugestia:

1. **Referencja zależna od tła** — zamiast jednej stałej referencji
   (skalibrowanej na jednym reżimie intensywności), referencja musi się
   adaptować do bieżących warunków tła, żeby zmiana samego poziomu
   ruchu (bez defektu) nie generowała fałszywego alarmu (naprawia
   zmierzony problem: FPR 5%→62% przy zmianie intensywności).
2. **Okno dopasowane do skali defektu** — zamiast jednego uniwersalnego
   rozmiaru okna, dobór okna/przesunięcia względem oczekiwanej skali
   czasowej wykrywanego defektu (naprawia zmierzony problem: brak
   wykrycia defektu okresowego T=100 przy oknie=60/przesunięcie=20).
3. **Kilka miar zamiast jednej** — łączenie entropii permutacyjnej z
   innymi, uzupełniającymi się miarami (np. CV, które w tym teście
   samo wykrywało to, czego entropia nie wykrywała) zamiast polegania
   na jednym wskaźniku o wąskim zakresie czułości.

Odpowiedź na konkretną prośbę: zdefiniować wymagania dla sensownego
operatora defektu i zastąpić "liczby pierwsze" czymś zakotwiczonym w
sygnale (struktura w przestrzeni fazowej / niestacjonarność).

## Wymagania (ustalone przed budową)

- **R1 — klasa "brak defektu" dobrze zdefiniowana**: konkretny rozkład
  referencyjny zbudowany z danych niezależnych od danych testowych, nie
  "cokolwiek wygląda normalnie".
- **R2 — poprawna kontrola negatywna**: próg kalibrowany na docelowy
  poziom fałszywych alarmów (5%) na zbiorze walidacyjnym ODDZIELONYM od
  zbioru kalibracyjnego, i dodatkowo sprawdzony na INNYM wariancie
  sygnału "bez defektu" — żeby wykryć, czy kalibracja generalizuje, czy
  działa tylko dla jednego konkretnego wariantu szumu.
- **R3 — przewaga nad prostymi miarami**: musi wykrywać to, czego nie
  wykrywają już przetestowane baseline'y (CV luk, odległość od
  płaszczyzny), albo dawać lepszy kontrast przy tym samym FPR.

## Nowy operator (zamiast liczb pierwszych)

**Entropia permutacyjna (Bandt & Pompe 2002)** liczona w oknie
przesuwnym, monitorowana jako dryf względem rozkładu referencyjnego.
To jednocześnie: (a) miara struktury w przestrzeni fazowej (wzorce
rangowe kolejnych próbek — ugruntowana metoda, stosowana w diagnostyce
uszkodzeń mechanicznych, EEG, sygnałach finansowych), i (b) miara
niestacjonarności (dryf tej miary względem referencji) — dokładnie
dwie rzeczy zaproponowane w miejsce liczb pierwszych, połączone w
jeden test.

## Wyniki

**R1/R2 — kalibracja i kontrola negatywna:**

| Test | Wynik |
|---|---|
| FPR na zbiorze walidacyjnym (ten sam proces co referencja) | 0,050 — dokładnie trafia w cel |
| FPR na NOWYM, niezależnym zbiorze testowym (ten sam proces) | 0,053 — **dobrze skalibrowany** |
| FPR na INNYM procesie "bez defektu" (ten sam typ szumu, inna intensywność) | **0,621 — kalibracja NIE generalizuje** |

**To jest najważniejszy, uczciwy wynik tego testu.** Operator jest
poprawnie skalibrowany — ale tylko dla DOKŁADNIE tego samego reżimu
statystycznego, na którym był kalibrowany. Wystarczy zmienić samo tło
(np. inna intensywność ruchu, żadnego realnego defektu) i fałszywy
alarm wystrzeliwuje z 5% do 62%. Entropia permutacyjna zliczonego
procesu Poissona zależy od średniej liczby zdarzeń w oknie — zmiana
intensywności tła zmienia tę entropię tak samo jak prawdziwy defekt.
**R1 nie jest w pełni spełnione**: klasa "brak defektu" jest
zdefiniowana wąsko (jeden konkretny reżim), nie ogólnie.

**R3 — wykrywanie defektów vs. baseline CV (z poprzedniego testu):**

| Scenariusz | Nowy operator (% okien-alarmów) | CV (z poprzedniego testu) |
|---|---|---|
| B) defekt klastrowy | **89,9%** — wyraźnie wykrywa | 3,4 (>1, poprawnie wykrywa) |
| C) defekt okresowy | **0,2% — PRAKTYCZNIE NIE WYKRYWA** | 0,07 (<1, **poprawnie i wyraźnie wykrywa**) |

Dla defektu klastrowego nowy operator działa dobrze — ale nie lepiej
niż już istniejący prosty CV. Dla defektu okresowego **nowy operator
przegrywa wyraźnie z trywialnym baseline'em** — entropia permutacyjna
w tej konfiguracji (okno=60, przesunięcie=20, m=4) jest niewrażliwa na
regularność odstępów w tym zakresie parametrów.

## Werdykt

**R2 spełnione częściowo, R3 niespełnione.** Ten konkretny kandydat
(entropia permutacyjna + dryf względem wąsko zdefiniowanej referencji)
nie przechodzi własnych wymagań: nie generalizuje na zmianę tła (R1/R2),
i nie pokazuje przewagi nad najprostszym możliwym baseline'em (R3) — w
jednym z dwóch scenariuszy defektu jest od niego wyraźnie gorszy.

To NIE oznacza, że entropia permutacyjna jest bezwartościowa — to
ugruntowana metoda z realnymi zastosowaniami. Oznacza, że **ten
konkretny, pierwszy projekt operatora** (naiwne porównanie do jednej
referencji, bez normalizacji względem zmiennego tła) ma dokładnie ten
sam rodzaj problemu, co poprzednie próby: działa tam, gdzie sygnał jest
oczywisty, i nie dodaje nic ponad prostszą alternatywę tam, gdzie
naprawdę byłoby to przydatne.

**Co byłoby potrzebne, żeby to naprawić** (nie zrobione w tym teście,
uczciwie odnotowane jako kierunek, nie wynik):
- normalizacja referencji względem lokalnego tła (np. adaptacyjna,
  krocząca referencja zamiast jednej stałej), żeby rozwiązać problem
  z R2;
- dobór parametrów (m, okno, przesunięcie) do konkretnej skali
  spodziewanego defektu zamiast jednego uniwersalnego ustawienia — dla
  scenariusza C prawdopodobnie inny dobór okna wykrywałby okresowość;
- test na kombinacji kilku miar (entropia + CV) zamiast jednej,
  żeby pokryć wzajemne słabości.

## Uruchomienie

```bash
python3 defect_operator.py
```

---

## v2 — wdrożenie trzech naprawi: wynik (nie czyste zwycięstwo)

Zaimplementowano wszystkie trzy punkty z sekcji "STATUS" powyżej:
1. **Referencja zależna od tła** — lokalny, przyczynowy z-score
   (mediana/MAD) liczony z K=15 POPRZEDNICH okien zamiast jednej stałej,
   globalnej referencji.
2. **Okno dopasowane do skali defektu** — dwie skale równolegle: KRÓTKA
   (okno=60) i DŁUGA (okno=300, ~3× okres defektu C).
3. **Kilka miar zamiast jednej** — entropia permutacyjna I współczynnik
   zmienności połączone regułą OR, progi dobrane Bonferronim (2,5%
   każda, żeby łącznie trafić w 5%).

### Wyniki (`defect_operator_v2.py`, jeden przebieg, seedy jak w kodzie)

| Test | v1 | v2 |
|---|---|---|
| FPR, ten sam reżim tła (walidacja) | 5,3% | 4,3% / 3,7% (obie skale) |
| **FPR, INNY reżim tła (rate 100→60), kluczowy test naprawy #1** | **62,1%** | **3,3% / 9,5% — NAPRAWIONE** |
| Wykrywanie C) defekt okresowy, kluczowy test naprawy #2+#3 | 0,2% | **60,5% / 54,3% — NAPRAWIONE** |
| Wykrywanie B) defekt klastrowy | 89,9% | **5,7% / 6,6% — NOWA REGRESJA** |

### Uczciwa interpretacja

**Dwie naprawy zadziałały dokładnie tak, jak przewidziano**: adaptacyjna
referencja lokalna rozwiązała problem generalizacji na zmianę tła
(62%→~3-10%), a dopasowanie okna do skali defektu + połączenie miar
rozwiązało brak wykrycia defektu okresowego (0,2%→~55-60%).

**Ale pojawił się nowy, zmierzony problem**: wykrywanie defektu
klastrowego spadło z 89,9% (v1) do ~6% (v2) — praktycznie zniknęło.
Przyczyna (mechanistyczna, nie zgadywana): w scenariuszu B defekty
klastrowe powtarzają się DOŚĆ CZĘSTO (400 wybuchów w całej serii).
Referencja krocząca (K=15 okien) uczy się ich jako "nowej normy"
szybciej, niż zdążą zostać uznane za anomalię — dokładnie ten sam
mechanizm, co znany w literaturze bezpieczeństwa problem "zatruwania"
adaptacyjnej linii bazowej (baseline poisoning) — jeśli "atak"/defekt
powtarza się częściej niż okno adaptacji, adaptacyjny detektor uczy się
go jako normalności. To jest fundamentalny kompromis: szybka adaptacja
(mała K) dobrze radzi sobie ze zmianą tła, ale źle z często
powtarzającymi się defektami; wolna adaptacja (duża K) działa odwrotnie
— żadna pojedyncza wartość K nie rozwiązuje obu naraz.

**Werdykt v2**: dwie z trzech naprawionych rzeczy naprawione i
zmierzone, jedna nowa regresja odkryta i zmierzona. To NIE jest czysty
sukces "v2 lepsze od v1" — to przesunięcie problemu, uczciwie
udokumentowane. Sensowny kierunek na v3 (niewykonany, tylko
zaproponowany): referencja krocząca odporna na własne wcześniejsze
detekcje — wykluczać z okna referencyjnego K poprzednich okien te,
które same zostały oflagowane jako anomalie (dokładnie ten sam wzorzec
naprawy co wcześniejszy "self-poisoning threshold" bug w
`TIMDR-Security-Module/timdr_security.py`, `_robust_loo_zscore`) —
zamiast pozwalać defektowi zanieczyszczać własną referencję.

### Uruchomienie v2

```bash
python3 -u defect_operator_v2.py
```

---

## v3 — naprawa regresji z v2: bufor odporny na własne detekcje (samo-wykluczanie)

**Hipoteza (zapisana przed uruchomieniem)**: wykluczyć z referencji
kroczącej okna, które same zostały wcześniej oflagowane jako anomalia
(dokładnie ten wzorzec naprawy, co `_robust_loo_zscore` w
`TIMDR-Security-Module`). Zastrzeżenie z góry: może nie wystarczyć,
jeśli defekty są na tyle częste, że "czysty" bufor nigdy się nie
zapełni albo regeneruje się bardzo wolno po zmianie reżimu.

### Wyniki

| Test | v1 | v2 | v3 |
|---|---|---|---|
| FPR, ten sam reżim (walidacja) | 5,3% | 3,7–4,3% | 7,6–8,3% (lekko gorzej) |
| FPR, INNY reżim tła (rate 100→60) | 62,1% | **3,3–9,5%** | **42,5–43,8% (regresja!)** |
| Wykrywanie B) klaster | 89,9% | 5,7–6,6% | **67,3% (KRÓTKA) — częściowo odzyskane** |
| Wykrywanie C) okresowy | 0,2% | 60,5% | **73,9% (KRÓTKA) — jeszcze lepiej** |

### Uczciwa interpretacja — dokładnie taki kompromis, jaki przewidziano

Samo-wykluczanie **częściowo odzyskało wykrywanie defektu klastrowego**
(5,7%→67,3%) i **poprawiło wykrywanie defektu okresowego** (60,5%→73,9%)
— zgodnie z hipotezą. Ale **przywróciło problem z v1**: FPR przy zmianie
tła podskoczył z powrotem do 42–44% (z 3–10% w v2).

**Mechanizm (zdiagnozowany, nie zgadywany)**: gdy CAŁY reżim tła się
zmienia (np. rate 100→60), na starcie WSZYSTKIE nowe okna wyglądają
"anomalnie" względem starego bufora (zbudowanego jeszcze w reżimie
rate=100). Samo-wykluczanie odrzuca je jako "anomalie" i NIGDY nie
pozwala im wejść do bufora — bufor zamraża się w starym reżimie i
generuje fałszywe alarmy w nieskończoność. To jest dokładnie
odwrotność problemu z v2 (v2 adaptował się ZA SZYBKO i "uczył się"
częstych defektów jako normy; v3 nie adaptuje się WCALE po prawdziwej
zmianie reżimu, bo myli "nowy uzasadniony reżim" z "defektem").

**To jest fundamentalny, znany w literaturze kompromis w adaptacyjnej
detekcji anomalii** (podobny do problemu "wolne futro" w filtrach
adaptacyjnych/wykrywaniu zmiany punktu): żaden pojedynczy, prosty
mechanizm (ani szybka adaptacja, ani samo-wykluczanie) nie rozwiązuje
jednocześnie "odróżnij defekt od częstego, ale prawdziwego szumu" i
"odróżnij defekt od uzasadnionej zmiany całego reżimu tła" — te dwa
wymagania ciągną w przeciwne strony przy tak prostej architekturze.
Rozwiązanie wymagałoby czegoś więcej niż jednej reguły kroczącej: np.
osobnego, jawnego detektora zmiany reżimu (change-point detection)
działającego RÓWNOLEGLE do detektora punktowych anomalii, żeby te dwa
zjawiska nie były mylone przez jeden mechanizm — nie zrobione w tej
sesji, zaproponowane jako kierunek na v4.

### Uruchomienie v3

```bash
python3 -u defect_operator_v3.py
```

---

## PODSUMOWANIE — co mamy na koniec (v1 → v2 → v3)

| Wersja | Co naprawiła | Co zepsuła / czego nie rozwiązała |
|---|---|---|
| **v1** (entropia permutacyjna, 1 stała referencja) | Nic — pierwszy szkic | FPR nie generalizuje na zmianę tła (62%); nie wykrywa defektu okresowego (0,2%) |
| **v2** (+ referencja adaptacyjna, +2 skale okna, +2 miary) | FPR przy zmianie tła (62%→3-10%); wykrywanie okresowego (0,2%→60%) | Wykrywanie klastrowego zapadło się (90%→6%) — "zatruwanie" baseline'u częstym defektem |
| **v3** (+ samo-wykluczanie oflagowanych okien z bufora) | Wykrywanie klastrowego częściowo odzyskane (6%→67%); okresowy jeszcze lepszy (60%→74%) | FPR przy zmianie tła znów wysoki (3-10%→42-44%) — bufor "zamraża się" po zmianie reżimu |

**Najważniejszy wniosek z całego ciągu v1→v2→v3**: to nie jest historia
"kolejna wersja jest strictly lepsza". To jest udokumentowany,
empirycznie zmierzony **kompromis inżynierski** — każda naprawiona
usterka odsłoniła nową, w przewidywalnym miejscu (adaptacja kontra
odporność na zatruwanie kontra odporność na zmianę reżimu). Żadna z
trzech wersji nie spełnia jednocześnie wszystkich trzech wymagań (R1
dobrze zdefiniowana klasa "brak defektu", R2 poprawna kontrola
negatywna generalizująca się na zmienne warunki, R3 przewaga nad
prostymi miarami na WSZYSTKICH typach defektu). To jest uczciwy,
falsyfikowalny wynik — nie "TIMDR to rozwiązał", tylko "oto dokładnie,
gdzie leżą granice tego podejścia i dlaczego".

W kontraście z resztą sesji: `../cosmology-filters` (dane rzeczywiste,
ugruntowana fizyka) i naprawiony `TIMDR-Security-Module` pokazują, że
rygorystyczne, testowane podejście MOŻE dawać solidne wyniki.
`../radar-prime-transfer` (transfer liczb pierwszych) pokazał, że nie
każdy pomysł da się uratować samą iteracją. Łańcuch v1-v4 poniżej
pokazuje coś pośredniego: architektura MOŻE rozwiązać część problemów
strukturalnych (patrz v4), ale ujawnia przy tym nowe, głębsze granice.

---

## v4 — architektura wielomodułowa (propozycja użytkownika): wynik

**Propozycja**: zamiast jednej linii bazowej robiącej wszystko, trzy
osobne moduły z fuzją decyzji:
1. **Detektor zmiany reżimu** — działa na DŁUGICH blokach (znacznie
   dłuższych niż typowy defekt), porównuje medianę CV kolejnych bloków
   formalnym progiem. Wykrywa TYLKO trwałe przesunięcia tła.
2. **Detektor punktowych anomalii/struktury** — ten sam mechanizm co
   v1/v2 (entropia permutacyjna + CV), ale referencja jest ZAMROŻONA na
   czas trwania bieżącego reżimu i aktualizuje się TYLKO gdy moduł 1
   potwierdzi prawdziwą zmianę reżimu.
3. **Fuzja** — zmiana reżimu i punktowa anomalia to dwie ROZDZIELONE
   decyzje; zmiana reżimu resetuje referencję modułu 2, ale sama nie
   jest raportowana jako "defekt".

### Wyniki

| Test | v1 | v2 | v3 | **v4** |
|---|---|---|---|---|
| FPR, stabilny reżim | 5,3% | 3,7–4,3% | 7,6–8,3% | **4,0%** |
| FPR PRZED zmianą reżimu | — | — | — | **3,3%** |
| **FPR PO prawdziwej zmianie reżimu** | 62,1%* | 3,3–9,5%* | 42,5–43,8%* | **3,9% — rozwiązane jednocześnie z powyższym** |
| Wykrywanie B) klaster | 89,9% | 5,7–6,6% | 67,3% | **2,4% — REGRESJA** |
| Wykrywanie C) okresowy | 0,2% | 60,5% | 73,9% | 46,3% (gorzej niż v2/v3) |

*v1/v2/v3 testowały zmianę reżimu jako CAŁY OSOBNY przebieg (inna
intensywność od początku do końca), nie jako przejście W TRAKCIE
jednego przebiegu — v4 to pierwsza wersja testowana na PRAWDZIWYM
przejściu reżimu w połowie sygnału, co jest twardszym i bardziej
realistycznym testem. Moduł 1 wykrył zmianę reżimu w 70% przebiegów.

### Najważniejszy wynik: architektura DZIAŁA tam, gdzie miała działać

**FPR przed zmianą reżimu (3,3%) i po zmianie (3,9%) są niemal
identyczne** — to jest dokładnie cel, którego v1/v2/v3 nie osiągnęły
jednocześnie. Rozdzielenie "czy tło się zmieniło" od "czy to okno jest
anomalią" faktycznie rozwiązuje kompromis, który blokował poprzednie
wersje. To potwierdza propozycję architektoniczną.

### Ale: nowy, głębszy problem ujawniony w scenariuszu B (klaster)

Wykrywanie defektu klastrowego ZAPADŁO SIĘ do 2,4% — gorzej nawet niż
v2. Diagnoza (zmierzona, nie zgadywana): moduł 2 buduje referencję
"braku defektu" z PIERWSZEGO bloku danych po (domniemanym) starcie
reżimu. Sprawdzono bezpośrednio: w scenariuszu B mediana CV w
PIERWSZYM bloku (4,28–5,40) jest praktycznie taka sama jak mediana CV
w CAŁEJ reszcie sygnału (4,54–4,62) — **pierwszy blok jest już
przesiąknięty defektami, bo w scenariuszu B defekty klastrowe
występują tak często (400 wybuchów na 2000 zdarzeń), że nie istnieje
żaden naprawdę "czysty" fragment sygnału, z którego dałoby się
zbudować referencję.**

To NIE jest błąd implementacji — to fundamentalne ograniczenie
WSZYSTKICH metod detekcji anomalii bez nadzoru (unsupervised): zakładają
one, że anomalie są RZADKIE względem normalnego zachowania. Gdy ten
warunek nie jest spełniony (jak w scenariuszu B, gdzie defekt jest
częścią większości sygnału, nie rzadkim wyjątkiem), sama koncepcja
"referencji bez defektu" przestaje mieć sens - niezależnie od tego, jak
wyrafinowana jest architektura wokół niej.

### Werdykt v4

Architektura wielomodułowa **rozwiązała dokładnie ten problem, do
którego została zaprojektowana** (współistnienie odporności na zmianę
reżimu i wykrywania częstych defektów) w JEDNYM konkretnym wymiarze
(zmiana reżimu) — i to jest realny, zmierzony sukces, nie retoryka.
Ale odsłoniła kolejną, głębszą granicę: żadna architektura oparta na
"referencji zbudowanej z danych" nie poradzi sobie, gdy defekt nie jest
rzadkim wyjątkiem, tylko dominującą częścią sygnału. To wymagałoby już
nie kolejnej poprawki mechanizmu, tylko innego założenia wyjściowego
(np. wiedzy z zewnątrz o tym, co jest "normą", zamiast wnioskowania
tego z samych danych) — wykracza poza zakres tego, co da się rozwiązać
samą architekturą detekcji anomalii.

### Uruchomienie v4

```bash
python3 -u defect_operator_v4.py
```
