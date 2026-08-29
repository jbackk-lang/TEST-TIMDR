# Test operatora torsji TIMDR (poprawiona definicja)

Po krytyce wcześniejszego diagramu ("Torsion: x×X=0" — notacja bez
sensu, plus pusta sekcja "Boundary Conditions") użytkownik przesłał
poprawioną, formalną definicję:

```
T(t) = [(ẋ(t) × ẍ(t)) · ẍ̇(t)] / ‖ẋ(t) × ẍ(t)‖²
```

(uzupełniono brakującą w transkrypcji trzecią pochodną — to standardowy
wzór **skręcenia Freneta-Serreta** dla krzywej w ℝ³, znany od dawna w
geometrii różniczkowej, założenie jawnie odnotowane).

**To jest inna sytuacja niż wcześniej.** To prawdziwy, dobrze
zdefiniowany obiekt matematyczny — nie numerologia, nie przypadkowa
notacja. Ograniczenie: wymaga sygnału 3D (iloczyn wektorowy działa
tylko w ℝ³) — użytkownik sam to zaznaczył ("sygnały wielowymiarowe,
np. IMU"). Ten test sprawdza empirycznie, czy operator (a) jest
poprawnie zaimplementowany, i (b) faktycznie coś wykrywa na
realistycznym, zaszumionym sygnale.

## Wyniki

**Testy 1–3 (poprawność matematyczna): WSZYSTKIE PRZESZŁY.**

| Test | Oczekiwanie | Wynik |
|---|---|---|
| Helisa (a=2, b=0.5) | κ=0,47059, τ=0,11765 (analitycznie) | κ=0,47059, τ=0,11765 — **zgodne co do 5 miejsca** |
| Linia prosta | ẋ×ẍ=0 (warunek brzegowy powinien to wyłapać) | max‖ẋ×ẍ‖=4,9×10⁻¹⁰ — **poprawnie ~0** |
| Elipsa płaska (z=0) | κ≠0, ale τ=0 (twierdzenie: krzywa płaska ma zerową torsję) | κ=0,504, max\|τ\|=0 — **dokładnie zgodne z teorią** |

Wniosek: operator jest zaimplementowany poprawnie i zgadza się z
ugruntowaną teorią. **To jest realna, sprawdzona matematyka** — inaczej
niż "x×X=0" z poprzedniego diagramu.

**Test 4 (defekt na tle szumu czujnika): TORSJA NIE WYKRYŁA DEFEKTU.**

Scenariusz: płaska elipsa + realistyczny szum IMU (σ=0,03, ~1% skali
ścieżki) + lokalny defekt skrętu poza płaszczyzną (amplituda 0,15, w
krótkim oknie czasowym).

| Metoda | Sygnał w oknie defektu | Tło | Kontrast |
|---|---|---|---|
| **Torsja τ(t)** | 48,62 | 48,90 | **0,99× — brak sygnału** |
| Krzywizna κ(t) (bez tła) | 10,14 | 10,02 | 1,01× — też brak |
| **Baseline: odległość od dopasowanej płaszczyzny** (bez różniczkowania) | 0,095 | 0,024 | **3,91× — wyraźnie wykrywa defekt** |

**Dlaczego torsja zawodzi**: wzór wymaga TRZECIEJ pochodnej. Numeryczne
różniczkowanie wzmacnia szum z każdym rzędem — przy trzeciej pochodnej
nawet umiarkowany szum czujnika (1% skali sygnału) całkowicie zalewa
sygnał geometryczny. To nie jest błąd implementacji (patrz testy 1–3,
bezszumowe) — to fundamentalna, dobrze znana w analizie numerycznej
własność różniczkowania zaszumionych danych.

**Test 5 (skan parametrów — czy to pech, czy fundamentalne
ograniczenie?)**: sprawdzono 7 kombinacji poziomu szumu (0,001–0,03) i
szerokości wygładzania Savitzky-Golay (21–101 próbek). Kontrast rósł
dopiero przy **jednoczesnym** obniżeniu szumu 30× (do 0,001) I
poszerzeniu okna wygładzania do 51 próbek — osiągając kontrast 2,98×.
To wciąż **gorzej niż trywialny baseline (3,91×) osiągnięty przy szumie
30× większym**. Innymi słowy: nawet w najbardziej sprzyjających
warunkach w tym skanie, torsja nie pobiła prostego, zero-różniczkowego
baseline'u działającego w warunkach dużo trudniejszych.

## Werdykt

**Poprawiona definicja torsji to prawdziwa, poprawnie zaimplementowana
matematyka — to trzeba przyznać wprost, w przeciwieństwie do
wcześniejszego diagramu.** Ale "matematycznie poprawne" i "praktycznie
użyteczne do wykrywania defektów w zaszumionym sygnale" to dwie różne
rzeczy, i tu operator nie daje wyniku: wymóg trzeciej pochodnej czyni go
z natury bardzo wrażliwym na szum, do tego stopnia, że w tym
eksperymencie **prosty baseline bez żadnego różniczkowania (odległość
od dopasowanej płaszczyzny) wygrywa wyraźnie, nawet przy dużo gorszym
stosunku sygnału do szumu**.

To nie przekreśla operatora torsji jako takiego — w czystych,
niskoszumowych danych (test 1, helisa) działa bezbłędnie, i mogą
istnieć zastosowania z bardzo czystym sygnałem (np. dane symulacyjne,
nie z prawdziwego czujnika) albo z dużo dłuższymi seriami czasowymi
pozwalającymi na mocniejsze wygładzanie bez utraty rozdzielczości
czasowej defektu. Ale w realistycznym scenariuszu czujnikowym (IMU z
typowym poziomem szumu) — dokładnie tam, gdzie miał być użyteczny wg
oryginalnej tezy — nie dorównuje najprostszej możliwej alternatywie.

## Uruchomienie

```bash
python3 torsion_experiment.py
```

## Ograniczenia tego testu

- Sprawdzono jeden typ defektu (lokalny bump poza płaszczyzną) i jeden
  typ szumu (biały, gaussowski, izotropowy). Inne typy defektów/szumu
  nie zostały przetestowane.
- Nie testowano operatora na prawdziwych danych IMU (tylko syntetyczne)
  — prawdziwe czujniki mają dodatkowe charakterystyki szumu (dryft,
  korelacje czasowe), które mogłyby zmienić wynik w obie strony.
- Filtr Savitzky-Golay to jedna z wielu metod różniczkowania
  numerycznego — bardziej zaawansowane metody (np. filtr Kalmana z
  modelem ruchu, TVD - total variation denoising) mogłyby dać lepsze
  wyniki, nie zostały tu przetestowane.
