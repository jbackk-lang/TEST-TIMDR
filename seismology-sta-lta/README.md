# Sejsmologia: STA/LTA jako test hipotezy "trzęsienie = rzadki sygnał"

Odpowiedź empiryczna na pytanie z rozmowy: czy przy ciągłym
monitorowaniu sejsmologicznym trzęsienie jest "rzadkim sygnałem"
(pasuje do założeń architektury v4 z `../defect-operator`), a rój
wstrząsów wtórnych łamie to założenie tak samo jak scenariusz B
(klaster) w tamtym teście?

**Metoda**: STA/LTA (short-term/long-term average) — prawdziwy,
standardowy algorytm sejsmologiczny (Allen, 1978), nie autorska
metoda. Użyty tu również jako niejawny test architektoniczny: STA/LTA
jest ILORAZEM, więc z definicji powinien być odporny na powolną zmianę
poziomu tła bez osobnego "modułu zmiany reżimu" jak w v4.

## Wyniki

**Test A — powolna zmiana reżimu tła (np. sztorm, poziom×2 w
połowie):**

| | FPR przed zmianą | FPR po zmianie |
|---|---|---|
| STA/LTA (próg kalibrowany na 2%) | 1,1% | 1,3% |

**STA/LTA jest z natury odporny na tę zmianę** — bez żadnego osobnego
modułu wykrywania zmiany reżimu. To jest prostsze i bardziej eleganckie
rozwiązanie problemu, który w `defect-operator` wymagał całej osobnej
architektury (v4, moduł 1) — ponieważ STA/LTA to iloraz, licznik i
mianownik skalują się razem, gdy zmienia się poziom tła.

**Test B — izolowane trzęsienie (kontrola pozytywna):**

Wykrycie: **100%**, fałszywy alarm poza oknem trzęsienia: 1,1%. Zgodne
z hipotezą "rzadki sygnał = działa dobrze".

**Test C — rój wstrząsów wtórnych wg prawa Omoriego:**

| | Wykrycie |
|---|---|
| Izolowane trzęsienie (test B) | 100% |
| Wczesne wstrząsy wtórne (<200 próbek od głównego wstrząsu, n=65) | 89% |
| Późne wstrząsy wtórne (≥200 próbek, n=35) | **37%** |

LTA (poziom tła): 1,07 (przed rojem) → 1,73 (+50 próbek, szczyt roju)
→ 1,32 (+500) → 0,95 (+1000, prawie wraca do bazowego poziomu).

## Uczciwa interpretacja — hipoteza z rozmowy potwierdzona częściowo, z ważnym zastrzeżeniem

**Degradacja wykrywalności podczas roju jest realna** (100%→37% dla
późnych wstrząsów) — to potwierdza ogólny kierunek hipotezy: rój
wstrząsów wtórnych rzeczywiście utrudnia detekcję względem izolowanego
przypadku.

**Ale mechanizm jest inny, niż zakładała prosta analogia do
scenariusza B z `defect-operator`.** Tam defekt klastrowy calkowicie
zniszczył referencję (bo referencja była budowana z danych zawierających
defekt). Tutaj STA/LTA nie zapada się do ~0% jak tamten test (2,4%) —
zatrzymuje się na 37% dla późnych wstrząsów, i nawet ROŚNIE do 89% dla
wczesnych, mimo że LTA jest tam NAJBARDZIEJ podniesione (1,73, szczyt).
Powód: wczesne wstrząsy nakładają się na siebie w czasie (widoczne w
generowanych czasach Omoriego — wiele zdarzeń w ciągu kilku-kilkunastu
próbek), więc ich energie się sumują w tym samym oknie STA, dając
silniejszy, łatwiej wykrywalny sygnał — mimo podwyższonego mianownika
LTA. Późniejsze wstrząsy są bardziej odosobnione w czasie, więc każdy
musi "wygrać" z tłem SAM, o umiarkowanej (losowej, 0,5–2,5) amplitudzie
— i część po prostu jest za słaba, niezależnie od kontekstu roju.

**Wniosek**: degradacja podczas roju jest potwierdzona, ale to NIE jest
ten sam mechanizm "zatrutej referencji", co w `defect-operator`
scenariusz B. STA/LTA (krótkie okno dopasowane do skali czasowej
pojedynczego zdarzenia) okazuje się bardziej odporne na ten konkretny
tryb awarii niż entropia permutacyjna/CV na zbinowanych zliczeniach
zdarzeń z poprzedniego testu — to samo zjawisko fizyczne (rój
zdarzeń), ale inna architektura detektora daje wyraźnie inny (lepszy)
wynik.

## Czy taki moduł można dołączyć do repo — tak, dołączony

Ten test jest teraz częścią `TEST-TIMDR` jako piąty, niezależny wątek.
W przeciwieństwie do poprzednich czterech, wykorzystuje PRAWDZIWY,
ugruntowany algorytm branżowy (STA/LTA) zamiast autorskiej metody — co
czyni go dobrym punktem odniesienia: pokazuje, że "architektura
dopasowana do skali zjawiska" (krótkie okno ≈ czas trwania pojedynczego
zdarzenia) radzi sobie z problemem częstych, nakładających się zdarzeń
wyraźnie lepiej niż podejście z `defect-operator` (okno znacznie
większe niż pojedyncze zdarzenie, zliczenia zamiast energii).

## Uruchomienie

```bash
python3 seismo_sta_lta.py
```

## Ograniczenia

- Model transjentu (tłumiona sinusoida) jest uproszczeniem realnej fali
  P/S/coda — prawdziwe sejsmogramy mają bogatszą strukturę częstotliwościową.
- Parametry prawa Omoriego (K, c, p) dobrano tak, by skala czasowa
  pasowała do STA_WIN/LTA_WIN w tej syntetycznej jednostce czasu — nie
  są to wartości z konkretnego, prawdziwego katalogu wstrząsów wtórnych.
- Nie testowano nakładania się fal (interferencji kodowej) na poziomie
  kształtu fali — tylko na poziomie sumowania energii, co jest
  uproszczeniem względem prawdziwego problemu "phase picking" podczas
  rojów, opisanego w literaturze sejsmologicznej.
