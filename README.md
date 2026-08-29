# TEST-TIMDR

## Werdykt końcowy (sesja 2026-08-29)

```
✔ TIMDR działa tam, gdzie dane mają stabilną fizykę (Cosmology, Security).
✘ TIMDR nie działa tam, gdzie operator jest źle dopasowany do dziedziny (Prime).
✘ TIMDR nie działa tam, gdzie operator wymaga wysokiego rzędu różniczkowania (Torsion).
✘ TIMDR nie działa jako pojedynczy detektor anomalii (v1→v3).
✔ TIMDR działa jako architektura wielomodułowa (v4), ale tylko gdy defekt jest rzadki.
```

Pięć zdań, pięć osobno zmierzonych wyników — żadne nie jest ogólnikiem.
Szczegóły i liczby uzasadniające każdą linijkę w odpowiednich
podfolderach niżej.

Repozytorium zbierające **wyniki empirycznych testów i audytów**
twierdzeń o TIMDR wykonanych w tej sesji — pięć niezależnych wątków,
każdy z pre-rejestracją, kontrolą negatywną i uczciwym raportem
niezależnie od wyniku. To nie jest kolekcja gotowych produktów — to
zapis tego, co faktycznie sprawdzono, co się potwierdziło, a co
zostało obalone lub tylko częściowo naprawione.

## Zawartość

### [`cosmology-filters/`](cosmology-filters/)
Filtry anomalii dla danych kosmologicznych zbudowane od zera, w
kontraście do numerologii znalezionej wcześniej w `GIA-TIMDR`. Oparte
na prawdziwych, cytowanych danych (Planck 2018, MESSENGER, SH0ES) z
propagacją niepewności. **Wynik: solidny.** Trzy filtry, w tym jedna
prawdziwa pozytywna kontrola (napięcie Hubble'a, >5σ, poprawnie
wykryte) i jeden przypadek uczciwej samo-falsyfikacji (naiwny model
"równe odstępy pików CMB" poprawnie odrzucony jako zbyt uproszczony).

### [`radar-prime-transfer/`](radar-prime-transfer/)
Test tezy "TIMDR wykrywa defekty strukturalne przez strukturę liczb
pierwszych" (transfer testu Craméra/Gallaghera z prawdziwych liczb
pierwszych do pozycji zdarzeń w sygnale radarowym). **Wynik:
obalona.** Metoda dała 100% fałszywych alarmów na czystym szumie —
gorzej niż trywialny współczynnik zmienności (jedna linijka kodu).

### [`torsion-operator/`](torsion-operator/)
Test poprawionej, formalnej definicji "torsji" TIMDR (skręcenie
Freneta-Serreta dla krzywej 3D). **Wynik: matematycznie poprawna, ale
praktycznie krucha.** Przeszła wszystkie testy analityczne (helisa,
linia prosta, płaska elipsa), ale na realistycznym zaszumionym sygnale
(defekt IMU) nie wykryła nic — wymóg trzeciej pochodnej wzmacnia szum
ponad użyteczność. Trywialny baseline (odległość od dopasowanej
płaszczyzny) wygrał wyraźnie.

### [`defect-operator/`](defect-operator/)
Najdłuższy wątek: budowa kandydata na ogólny "operator defektu" od
podstaw, zgodnie z jawnie zdefiniowanymi wymaganiami (dobrze określona
klasa "brak defektu", poprawna kontrola negatywna, przewaga nad
prostymi miarami). Cztery iteracje (v1→v4), każda naprawiająca
zmierzony problem poprzedniej i odsłaniająca nowy:

| Wersja | Kluczowa zmiana | Naprawiła | Ujawniła |
|---|---|---|---|
| v1 | entropia permutacyjna, 1 stała referencja | — | brak generalizacji FPR; nie wykrywa defektu okresowego |
| v2 | + referencja adaptacyjna, 2 skale, 2 miary | generalizację FPR; defekt okresowy | zapadnięcie wykrywania defektu klastrowego |
| v3 | + samo-wykluczanie oflagowanych okien | częściowo defekt klastrowy | powrót problemu z generalizacją FPR |
| v4 | + osobny moduł detekcji zmiany reżimu (architektura wielomodułowa) | **jednoczesną odporność na zmianę reżimu I stabilny FPR** | fundamentalną granicę: żadna referencja "z danych" nie działa, gdy defekt nie jest rzadki |

**Wynik końcowy**: architektura wielomodułowa (v4) rozwiązała dokładnie
ten kompromis, do którego została zaprojektowana — ale odsłoniła
granicę głębszą niż dobór architektury: klasyczne założenie każdej
metody detekcji anomalii bez nadzoru (anomalie muszą być rzadkie)
przestaje działać, gdy nie jest spełnione, niezależnie od
wyrafinowania architektury wokół niego.

### [`seismology-sta-lta/`](seismology-sta-lta/)
Test pytania z rozmowy: przy ciągłym monitorowaniu sejsmologicznym,
czy trzęsienie jest "rzadkim sygnałem" (pasuje do założeń v4), a rój
wstrząsów wtórnych łamie to założenie jak scenariusz B (klaster) w
`defect-operator`? Użyto PRAWDZIWEGO, standardowego algorytmu
sejsmologicznego (STA/LTA, Allen 1978), nie autorskiej metody.
**Wynik: hipoteza częściowo potwierdzona, z ważnym zastrzeżeniem.**
STA/LTA jako iloraz jest z natury odporny na powolną zmianę tła (bez
osobnego modułu regime-change, w przeciwieństwie do `defect-operator`).
Izolowane trzęsienie: 100% wykrycia. Rój wstrząsów wtórnych: realna
degradacja (do 37% dla późnych, odosobnionych wstrząsów), ale NIE
katastroficzne zapadnięcie jak w scenariuszu B (2,4%) — mechanizm
okazał się inny niż "zatruta referencja": krótkie okno STA dopasowane
do skali pojedynczego zdarzenia daje wyraźnie lepszą odporność niż
zliczenia/entropia na dużych oknach z poprzedniego testu.

## Zasada wspólna dla wszystkich pięciu wątków

Pre-rejestracja (obiekt/metryka/model zerowy ustalone przed
uruchomieniem) → uruchomienie raz → raport niezależnie od tego, czy
wynik jest wygodny. Dwa wątki dały wynik solidny (cosmology-filters,
częściowo defect-operator v4 i seismology-sta-lta), dwa dały
falsyfikację (radar-prime-transfer, torsion-operator jako praktyczne
narzędzie), a defect-operator pokazał, że nawet naprawiona architektura
ma granicę strukturalną, nie tylko techniczną — natomiast
seismology-sta-lta pokazał, że ta sama granica (częste, nakładające się
zdarzenia) może być złagodzona, choć nie usunięta, przez dobór
architektury dopasowanej do skali zjawiska.
