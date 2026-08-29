# Test transferu: "widmo liczb pierwszych" → defekty radarowe

Odpowiedź empiryczna na tezę z syntezy o TIMDR w 6G/radarze/AI:
*"DSP nie widzi struktury [liczb pierwszych], ML nie widzi geometrii,
TIMDR wykrywa defekty strukturalne"*. Wcześniejszy krytyczny wyrok (bez
uruchamiania kodu) ocenił to jako nieuzasadnione przeniesienie wyniku
matematycznego z teorii liczb do sygnałów radarowych. Ten eksperyment
**sprawdza to empirycznie**, zamiast zgadywać — zgodnie z zasadą sesji
"zawsze uruchom kod, nie zakładaj".

## Metoda

Kod testu Craméra/Gallaghera (`_normalized_gaps`, `_ks_two_sided_vs_exp1`)
skopiowany **1:1** z `math-validator-3.0/filters/prime_spectrum_filter.py`
(dokładnie ta sama implementacja, która wcześniej w tej sesji poprawnie
wykryła realną strukturę w prawdziwych liczbach pierwszych). Zastosowany
tu do pozycji "zdarzeń" (indeksów próbek) w trzech syntetycznych
scenariuszach radarowych (N=2000 zdarzeń każdy, seed=2026):

- **A) Szum** — jednorodny proces Poissona (kontrola negatywna, brak
  defektu).
- **B) Defekt klastrowy** — proces Neyman-Scott (wybuchy zdarzeń w
  ciasnych grupach — model realnego zakłócenia typu burst).
- **C) Defekt okresowy** — stały okres + jitter (model artefaktu
  zegara/jammingu).

Porównanie z dwoma prostymi, standardowymi narzędziami DSP: współczynnik
zmienności CV (jedna linijka kodu) i funkcja korelacji par (standardowe
narzędzie do wykrywania okresowości/klastrowania).

## Wyniki (jeden przebieg, seed=2026, reprodukowalne)

| Scenariusz | TRANSFER (KS vs Exp(1)) | BASELINE CV | BASELINE korelacja par |
|---|---|---|---|
| A) Szum (brak defektu) | **p=0 — "ODRZUCA", flaguje jako defekt** | 1,007 → poprawnie: losowy | z=2,88 → poprawnie: brak struktury |
| B) Defekt klastrowy | p≈9×10⁻²⁶⁵ — flaguje jako defekt | 3,399 → poprawnie: klastrowanie | z=9,66 → poprawnie: silna struktura |
| C) Defekt okresowy | p=0 — flaguje jako defekt | 0,071 → poprawnie: regularny/okresowy | z=3,24 → słaby sygnał |

## Werdykt

**Przeniesienie NIE działa — i to gorzej niż "nie dodaje wartości": daje
fałszywy alarm na czystym szumie.** Test Craméra/KS oznacza jako
"nielosowe" WSZYSTKIE TRZY scenariusze, łącznie z kontrolą negatywną
(czysty proces Poissona, zero realnego defektu). To jest 100% fałszywych
alarmów na próbie kontrolnej w tym przebiegu — metoda nie rozróżnia
"defektu" od "normalnego szumu tła", czyli nie działa jako filtr w ogóle.

**Dlaczego tak się dzieje (mechanistyczne wyjaśnienie, nie tylko obserwacja):**
normalizacja `gap/log(pozycja)` jest skalibrowana pod GĘSTOŚĆ prawdziwych
liczb pierwszych, która maleje jak ~1/log(x). Pozycje zdarzeń w sygnale
radarowym (nawet czysto losowe, proces Poissona) mają w tym eksperymencie
w przybliżeniu STAŁĄ gęstość, nie malejącą jak 1/log(x). Zastosowanie
normalizacji zaprojektowanej dla jednego prawa gęstości do procesu
rządzącego się zupełnie innym prawem gęstości systematycznie zniekształca
rozkład luk z dala od Exp(1) — niezależnie od tego, czy w danych jest
jakakolwiek prawdziwa struktura. To nie jest przypadek ani błąd
implementacji — to fundamentalne niedopasowanie założeń modelu do nowej
dziedziny.

**W przeciwieństwie do tego, oba proste baseline'y (CV, korelacja par)
poprawnie zdiagnozowały wszystkie trzy scenariusze** — CV dało trzy
czysto rozróżnialne wartości (1,0 / 3,4 / 0,07) dokładnie odpowiadające
trzem różnym reżimom (losowy / klastrowy / okresowy), jedną linijką kodu,
bez żadnej maszynerii liczb pierwszych.

**Ostateczna odpowiedź na pytanie z syntezy**: teza "TIMDR wykrywa
defekty strukturalne tam, gdzie DSP/ML nie widzą" jest w tym konkretnym
mechanizmie (transfer testu Craméra/Gallaghera) **obalona** — metoda nie
tylko nie przewyższa istniejących narzędzi DSP, ale jest od nich gorsza
(fałszywy alarm na czystym szumie), podczas gdy najprostsze możliwe
narzędzie DSP (współczynnik zmienności) działa bezbłędnie na tym samym
zadaniu.

## Uruchomienie

```bash
python3 prime_transfer_experiment.py
```

## Ograniczenia tego testu (uczciwie)

- Trzy scenariusze to reprezentatywne, ale nie wyczerpujące modele
  defektów radarowych — inne rodzaje sygnałów (np. slabsze/subtelniejsze
  defekty, mieszanki scenariuszy) nie zostały przetestowane.
- Test dotyczy KONKRETNEGO mechanizmu przeniesienia (test Craméra/KS na
  znormalizowanych lukach pozycji). Nie wyklucza to, że jakiś INNY,
  starannie zaprojektowany sposób wykorzystania idei "struktury liczb
  pierwszych" mógłby zadziałać — ale ten najbardziej naturalny, dosłowny
  transfer (którego użyłby ktoś czytający oryginalną tezę) nie działa i
  jest gorszy od trywialnej alternatywy.
