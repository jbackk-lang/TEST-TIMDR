"""
Operator defektu v2 - naprawa trzech zmierzonych problemow z v1
(zapisanych w TIMDR-Defect-Operator-Candidate/README.md jako
falsyfikacja v1):

  1. REFERENCJA ZALEZNA OD TLA: zamiast jednej globalnej, stalej
     referencji, uzywamy LOKALNEJ, KROCZACEJ referencji (mediana+MAD z
     K poprzednich okien, przyczynowo - tylko przeszlosc, bez
     zagladania w przyszlosc) - jesli tlo powoli zmienia intensywnosc,
     referencja podaza za nim, i nie generuje falszywego alarmu.
  2. OKNO DOPASOWANE DO SKALI DEFEKTU: dwie skale okna rownolegle -
     KROTKA (window=60) do defektow krotkotrwalych/klastrowych, DLUGA
     (window=300, ~3x okres defektu C) do defektow okresowych/wolnych.
  3. KILKA MIAR ZAMIAST JEDNEJ: entropia permutacyjna (PE) ORAZ
     wspolczynnik zmiennosci (CV) liczone rownolegle w kazdym oknie,
     polaczone regula OR z progami dobranymi Bonferronim (kazda miara
     kalibrowana na polowe docelowego FPR), zeby wykorzystac wzajemnie
     uzupelniajace sie czulosci obu miar.

Kalibracja i test - DOKLADNIE ten sam protokol rygoru co w v1: kalibracja
na jednym zbiorze, walidacja na NIEZALEZNYM zbiorze tego samego reżimu,
i (kluczowy test tej wersji) na INNYM rezimie tla (inna intensywnosc) -
zeby sprawdzic, czy problem z v1 (FPR 5%->62% przy zmianie tla) zostal
naprawiony.
"""
import numpy as np
from itertools import permutations
import math

def permutation_entropy(x, m=4, tau=1):
    n = len(x)
    L = n - (m - 1) * tau
    if L < 10:
        return np.nan
    perms = {}
    for i in range(L):
        window = x[i:i + m * tau:tau]
        pattern = tuple(np.argsort(window))
        perms[pattern] = perms.get(pattern, 0) + 1
    counts = np.array(list(perms.values()), dtype=float)
    probs = counts / counts.sum()
    H = -np.sum(probs * np.log2(probs))
    return H / math.log2(math.factorial(m))

def cv_of_gaps_from_counts(counts):
    """CV liczony na 'lukach' miedzy zdarzeniami zrekonstruowanych z
    binowanego ciagu liczby zdarzen w oknie (przyblizenie - dla
    spojnosci z CV z v1, ktory liczyl CV surowych lukow pozycji)."""
    # aproksymacja: traktujemy sam ciag counts jako sygnal i liczymy
    # CV jego wartosci - to jest miara regularnosci gestosci zdarzen,
    # rozny formalnie od CV lukow, ale tej samej rodziny (dyspersja).
    if counts.mean() == 0:
        return np.nan
    return counts.std() / (counts.mean() + 1e-9)

def sliding_features(rate, window, step, m=4):
    centers, pe_vals, cv_vals = [], [], []
    for start in range(0, len(rate) - window, step):
        seg = rate[start:start + window]
        pe_vals.append(permutation_entropy(seg, m))
        cv_vals.append(cv_of_gaps_from_counts(seg))
        centers.append(start + window // 2)
    return np.array(centers), np.array(pe_vals), np.array(cv_vals)

def adaptive_zscores(values, trailing_k=15):
    """Lokalny, przyczynowy z-score wzgledem mediany/MAD z K
    POPRZEDNICH okien (nie globalnej, stalej referencji) - naprawia
    problem #1."""
    z = np.full(len(values), np.nan)
    for i in range(trailing_k, len(values)):
        hist = values[i - trailing_k:i]
        hist = hist[~np.isnan(hist)]
        if len(hist) < 5:
            continue
        med, mad = np.median(hist), np.median(np.abs(hist - np.median(hist)))
        mad = mad if mad > 1e-9 else 1e-9
        z[i] = abs(values[i] - med) / (1.4826 * mad)
    return z

def positions_to_rate_series(positions, bin_width=20, total_len=200000):
    bins = np.arange(0, total_len, bin_width)
    counts, _ = np.histogram(positions, bins=bins)
    return counts.astype(float)

def scenario_A(seed, rate_scale=100.0):
    r = np.random.default_rng(seed)
    gaps = r.exponential(scale=rate_scale, size=2000)
    return np.cumsum(gaps) + 1000

def scenario_B(seed):
    r = np.random.default_rng(seed)
    n_bursts = 2000 // 5
    burst_gaps = r.exponential(scale=500.0, size=n_bursts)
    burst_centers = np.cumsum(burst_gaps) + 1000
    positions = []
    for c in burst_centers:
        k = r.poisson(5) + 1
        offsets = r.normal(0, 5, size=k)
        positions.extend(c + offsets)
    return np.sort(np.array(positions))[:2000]

def scenario_C(seed):
    r = np.random.default_rng(seed)
    T = 100.0
    jitter = r.normal(0, 5, size=2000)
    return np.sort(1000 + T * np.arange(2000) + jitter)

SCALES = [("KROTKA", 60, 20), ("DLUGA", 300, 100)]
TRAILING_K = 15

def detect(positions, thresholds):
    """thresholds: dict {(scale_name, measure): próg z}. Zwraca odsetek
    okien oflagowanych (po zsumowaniu obu skal, bez podwojnego liczenia
    pozycji) - uproszczenie: raportujemy oddzielnie per skala i OR."""
    rate = positions_to_rate_series(positions)
    flags_per_scale = {}
    for name, window, step in SCALES:
        _, pe, cv = sliding_features(rate, window, step)
        z_pe = adaptive_zscores(pe, TRAILING_K)
        z_cv = adaptive_zscores(cv, TRAILING_K)
        thr_pe = thresholds[(name, "PE")]
        thr_cv = thresholds[(name, "CV")]
        flag = (z_pe > thr_pe) | (z_cv > thr_cv)
        flags_per_scale[name] = flag
    return flags_per_scale

# ---- KALIBRACJA (na scenariuszu A, rate=100) ----
print("=== KALIBRACJA progow (per skala, per miara) na scenariuszu A rate=100 ===")
target_fpr_per_measure = 0.025  # Bonferroni: 2 miary -> 0.05 total per skala
thresholds = {}
for name, window, step in SCALES:
    all_z_pe, all_z_cv = [], []
    for seed in range(100, 130):
        rate = positions_to_rate_series(scenario_A(seed))
        _, pe, cv = sliding_features(rate, window, step)
        z_pe = adaptive_zscores(pe, TRAILING_K)
        z_cv = adaptive_zscores(cv, TRAILING_K)
        all_z_pe.extend(z_pe[~np.isnan(z_pe)])
        all_z_cv.extend(z_cv[~np.isnan(z_cv)])
    thr_pe = np.quantile(all_z_pe, 1 - target_fpr_per_measure)
    thr_cv = np.quantile(all_z_cv, 1 - target_fpr_per_measure)
    thresholds[(name, "PE")] = thr_pe
    thresholds[(name, "CV")] = thr_cv
    print(f"  skala {name}: prog PE={thr_pe:.3f}, prog CV={thr_cv:.3f}")

# ---- WALIDACJA: ten sam rezim (rate=100), niezalezne seedy ----
print("\n=== R2: FPR na NIEZALEZNYM zbiorze testowym, TEN SAM rezim (rate=100) ===")
for name, window, step in SCALES:
    fprs = []
    for seed in range(300, 320):
        flags = detect(scenario_A(seed), thresholds)
        fprs.append(np.mean(flags[name]))
    print(f"  skala {name}: FPR={np.mean(fprs):.3f} (cel: ~0.05)")

# ---- KLUCZOWY TEST: INNY rezim tla (rate=60) - to zawiodlo w v1 ----
print("\n=== R1/R2 (KLUCZOWY TEST NAPRAWY): FPR przy INNYM tle (rate=60, bez defektu) ===")
for name, window, step in SCALES:
    fprs = []
    for seed in range(400, 420):
        flags = detect(scenario_A(seed, rate_scale=60.0), thresholds)
        fprs.append(np.mean(flags[name]))
    print(f"  skala {name}: FPR={np.mean(fprs):.3f} (w v1 bylo 0.621 - CEL: bliżej 0.05)")

# ---- R3: wykrywanie defektow B i C ----
print("\n=== R3: wykrywanie defektow (obie skale) ===")
for label, fn in [("B) klaster", scenario_B), ("C) okresowy", scenario_C)]:
    det_short, det_long = [], []
    for seed in range(500, 515):
        flags = detect(fn(seed), thresholds)
        det_short.append(np.mean(flags["KROTKA"]))
        det_long.append(np.mean(flags["DLUGA"]))
    print(f"  {label}: skala KROTKA={np.mean(det_short):.3f}, skala DLUGA={np.mean(det_long):.3f}")
