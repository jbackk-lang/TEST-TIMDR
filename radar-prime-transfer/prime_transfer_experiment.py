"""
PRE-REJESTRACJA (przed uruchomieniem)
=====================================
Test transferu "widma liczb pierwszych" (test Kolmogorowa-Smirnowa
znormalizowanych luk vs Exponencjalny(1), model Craméra/Gallaghera —
kod SKOPIOWANY 1:1 z `math-validator-3.0/filters/prime_spectrum_filter.py`,
funkcje `_normalized_gaps` i `_ks_two_sided_vs_exp1`) do wykrywania
"defektów strukturalnych" w impulsach radarowych.

Powód testu: w rozmowie padła teza (synteza o TIMDR w 6G/radarze/AI):
"DSP nie widzi struktury [liczb pierwszych], ML nie widzi geometrii,
TIMDR wykrywa defekty strukturalne". Wcześniejszy krytyczny wyrok
(bez uruchamiania kodu) ocenił to jako nieuzasadnione przeniesienie
wyniku matematycznego z jednej dziedziny (teoria liczb) do zupełnie
innej (sygnały radarowe) bez wykazanego związku. Ten skrypt
SPRAWDZA to empirycznie zamiast zgadywać.

OBIEKTY: trzy scenariusze generowania pozycji "zdarzeń" (indeksów
próbek) w syntetycznym ciągu radarowym, N=2000 zdarzeń każdy, zakres
pozycji rzędu 10^3-10^5 (realistyczny rząd wielkości dla indeksów
próbek w przechwyconym oknie radarowym):

  A) SZUM (kontrola negatywna) — jednorodny proces Poissona, średni
     odstęp 100 próbek. Brak realnego defektu — tylko losowe
     fluktuacje tła. Filtr NIE POWINIEN niczego tu wykryć.
  B) DEFEKT KLASTROWY — proces Neyman-Scott (centra wybuchów ~Poisson,
     każdy wybuch = kilka zdarzeń w ciasnym otoczeniu). Realistyczny
     model fizycznego defektu (np. przejściowe zakłócenie EM, seria
     błędów bitowych) — niologiczny, nieokresowy, ale REALNIE
     nielosowy.
  C) DEFEKT OKRESOWY — pozycje = stały okres T=100 próbek + mały
     jitter gaussowski. Model artefaktu zegara / okresowego
     zakłócenia (jamming) — również REALNIE nielosowy.

METRYKI (ustalone przed uruchomieniem):
  1. TRANSFER: dokładnie ten sam kod co w prime_spectrum_filter.py.
  2. BASELINE 1: współczynnik zmienności CV = std(gaps)/mean(gaps)
     surowych (nieznormalizowanych) luk — jedna linijka kodu,
     standardowe narzędzie w teorii niezawodności/kolejek.
  3. BASELINE 2: funkcja korelacji par (pair correlation / histogram
     wszystkich parowych odległości do max_lag) — standardowe
     narzędzie DSP do wykrywania okresowości/klastrowania.

PYTANIE: czy TRANSFER poprawnie odróżnia A (brak defektu) od B/C
(defekt)? Czy dodaje cokolwiek ponad dużo prostsze, istniejące
narzędzia DSP (baseline 1 i 2)?

Jeden przebieg, seed ustalony z góry (2026), wynik raportowany
uczciwie niezależnie od tego, co pokaże.
"""

import numpy as np
from math import log, sqrt, exp

# --- skopiowane 1:1 z math-validator-3.0/filters/prime_spectrum_filter.py ---
def _normalized_gaps(primes, gaps):
    """x_n = gap_n / log(p_n) - dokladnie ta sama normalizacja co dla
    prawdziwych liczb pierwszych, zastosowana tu do pozycji zdarzen w
    sygnale radarowym zamiast do wartosci liczb pierwszych."""
    return [g / log(p) for g, p in zip(gaps, primes[:-1])]


def _ks_two_sided_vs_exp1(x):
    n = len(x)
    if n == 0:
        return None, None
    xs = sorted(x)
    d_plus = max((i + 1) / n - (1 - exp(-xs[i])) for i in range(n))
    d_minus = max((1 - exp(-xs[i])) - i / n for i in range(n))
    d = max(d_plus, d_minus)
    en = sqrt(n)
    term = (en + 0.12 + 0.11 / en) * d
    q = 0.0
    for k in range(1, 101):
        term_k = ((-1) ** (k - 1)) * exp(-2 * k * k * term * term)
        q += term_k
        if abs(term_k) < 1e-12:
            break
    p = max(0.0, min(1.0, 2 * q))
    return d, p
# --- koniec kopii ---


rng = np.random.default_rng(2026)
N_EVENTS = 2000


def scenario_A_poisson_noise():
    gaps = rng.exponential(scale=100.0, size=N_EVENTS)
    return np.cumsum(gaps) + 1000


def scenario_B_cluster_burst():
    n_bursts = N_EVENTS // 5
    burst_gaps = rng.exponential(scale=500.0, size=n_bursts)
    burst_centers = np.cumsum(burst_gaps) + 1000
    positions = []
    for c in burst_centers:
        k = rng.poisson(5) + 1
        offsets = rng.normal(0, 5, size=k)
        positions.extend(c + offsets)
    positions = np.sort(np.array(positions))
    return positions[positions > 0][:N_EVENTS]


def scenario_C_periodic_jitter():
    T = 100.0
    jitter = rng.normal(0, 5, size=N_EVENTS)
    positions = 1000 + T * np.arange(N_EVENTS) + jitter
    return np.sort(positions)


def autocorr_peak_via_pairwise_gaps(positions, max_lag=400):
    """Funkcja korelacji par: histogram WSZYSTKICH parowych odleglosci
    (nie tylko sasiednich) do max_lag - standardowe narzedzie do
    wykrywania okresowosci/klastrowania w procesach punktowych."""
    positions = np.sort(positions)
    diffs = positions[:, None] - positions[None, :]
    diffs = diffs[diffs > 0]
    diffs = diffs[diffs <= max_lag]
    hist, _ = np.histogram(diffs, bins=np.arange(0, max_lag + 2))
    search = hist[5:]
    if len(search) == 0 or search.std() == 0:
        return None, 0, float("nan")
    best_lag = int(np.argmax(search)) + 5
    background_mean, background_std = search.mean(), search.std()
    peak_z = (hist[best_lag] - background_mean) / background_std if background_std > 0 else float("nan")
    return best_lag, int(hist[best_lag]), peak_z


def analyze(name, positions):
    positions = np.asarray(sorted(positions), dtype=float)
    positions = positions[positions > 1]
    gaps = np.diff(positions)
    gaps = gaps[gaps > 0]
    positions_for_norm = positions[: len(gaps) + 1]

    x = _normalized_gaps(list(positions_for_norm), list(gaps))
    d, p = _ks_two_sided_vs_exp1(x)
    cv = np.std(gaps) / np.mean(gaps)
    best_lag, peak_count, peak_z = autocorr_peak_via_pairwise_gaps(positions)

    print(f"=== {name} ===")
    print(f"  N zdarzen: {len(positions)}, N lukow: {len(gaps)}")
    print(
        f"  [TRANSFER] Cramer/KS vs Exp(1): D={d:.4f}, p={p:.4g}  "
        f"({'ODRZUCA Exp(1) -> flaguje jako *nielosowe*' if p < 0.01 else 'NIE odrzuca -> wyglada jak proces losowy'})"
    )
    print(
        f"  [BASELINE 1] CV surowych lukow: {cv:.4f}  "
        f"({'~1 => Poisson/losowy' if 0.8 < cv < 1.2 else ('<1 => regularny/okresowy' if cv < 0.8 else '>1 => klastrowanie/nadmierna dyspersja')})"
    )
    print(
        f"  [BASELINE 2] korelacja par: najlepszy lag={best_lag}, liczba par={peak_count}, z={peak_z:.2f}  "
        f"({'WYRAZNY PIK - struktura wykryta' if peak_z > 5 else 'brak wyraznego piku'})"
    )
    print()
    return {"name": name, "ks_p": p, "cv": cv, "ac_z": peak_z}


if __name__ == "__main__":
    results = [
        analyze("A) SZUM (Poisson, kontrola negatywna)", scenario_A_poisson_noise()),
        analyze("B) DEFEKT KLASTROWY (Neyman-Scott burst)", scenario_B_cluster_burst()),
        analyze("C) DEFEKT OKRESOWY (T=100 + jitter)", scenario_C_periodic_jitter()),
    ]
    print("=== PODSUMOWANIE ===")
    for r in results:
        print(r["name"], "-> KS p=%.4g, CV=%.3f, AC_z=%.2f" % (r["ks_p"], r["cv"], r["ac_z"]))
