"""
Operator defektu v3 - naprawa regresji z v2 (wykrywanie defektu B
klastrowego spadlo z 89.9% do ~6%, bo referencja kroczaca "uczyla sie"
czestych bustow jako normy - klasyczny problem "zatruwania" baseline'u,
ten sam mechanizm co juz raz naprawiany self-poisoning threshold bug w
TIMDR-Security-Module/_robust_loo_zscore).

NAPRAWA v3: referencja kroczaca buduje sie TYLKO z okien, ktore SAME
NIE zostaly oflagowane jako anomalia w momencie ich oceny (sekwencyjne,
przyczynowe wykluczanie) - okno raz uznane za defekt NIE wchodzi do
przyszlej referencji. To dokladnie ten sam wzorzec naprawy co w
TIMDR-Security-Module.

PRE-REJESTROWANA HIPOTEZA (przed uruchomieniem): to MOZE nie
wystarczyc, jesli defekty sa NA TYLE czeste, ze wiekszosc (>50%) okien
w danym rejonie sygnalu jest nimi dotknieta - wtedy nawet mediana z
"czystych" okien moze byc zbudowana z bardzo malej, niereprezentatywnej
próbki, albo bufor moze sie nigdy nie zapelnic czystymi oknami. Test
sprawdza to empirycznie, nie zaklada z gory sukcesu.
"""
import numpy as np
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

def cv_of_counts(counts):
    if counts.mean() == 0:
        return np.nan
    return counts.std() / (counts.mean() + 1e-9)

def sliding_features(rate, window, step, m=4):
    centers, pe_vals, cv_vals = [], [], []
    for start in range(0, len(rate) - window, step):
        seg = rate[start:start + window]
        pe_vals.append(permutation_entropy(seg, m))
        cv_vals.append(cv_of_counts(seg))
        centers.append(start + window // 2)
    return np.array(centers), np.array(pe_vals), np.array(cv_vals)

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

def sequential_self_excluding_z(values, thr, trailing_k=TRAILING_K):
    """Sekwencyjny, przyczynowy z-score wzgledem bufora ZLOZONEGO
    WYLACZNIE Z OKIEN WCZESNIEJ NIE-OFLAGOWANYCH. Zwraca (z_array,
    flag_array, frac_buffer_from_clean) - to ostatnie mowi, jak czesto
    bufor byl w ogole "czysty" (informacja diagnostyczna, nie tylko
    wynik)."""
    n = len(values)
    z = np.full(n, np.nan)
    flags = np.zeros(n, dtype=bool)
    buffer = []
    buffer_sizes = []
    for i in range(n):
        v = values[i]
        buffer_sizes.append(len(buffer))
        if np.isnan(v) or len(buffer) < 5:
            if not np.isnan(v):
                buffer.append(v)
                if len(buffer) > trailing_k:
                    buffer.pop(0)
            continue
        med = np.median(buffer)
        mad = np.median(np.abs(np.array(buffer) - med))
        mad = mad if mad > 1e-9 else 1e-9
        zi = abs(v - med) / (1.4826 * mad)
        z[i] = zi
        flagged = zi > thr
        flags[i] = flagged
        if not flagged:
            buffer.append(v)
            if len(buffer) > trailing_k:
                buffer.pop(0)
        # jesli flagged: NIE dodajemy do bufora (self-exclusion, naprawa v3)
    return z, flags, np.mean(buffer_sizes) / trailing_k

def detect_v3(positions, thresholds):
    rate = positions_to_rate_series(positions)
    flags_per_scale = {}
    buf_health = {}
    for name, window, step in SCALES:
        _, pe, cv = sliding_features(rate, window, step)
        thr_pe, thr_cv = thresholds[(name, "PE")], thresholds[(name, "CV")]
        _, flag_pe, health_pe = sequential_self_excluding_z(pe, thr_pe)
        _, flag_cv, health_cv = sequential_self_excluding_z(cv, thr_cv)
        flags_per_scale[name] = flag_pe | flag_cv
        buf_health[name] = (health_pe, health_cv)
    return flags_per_scale, buf_health

# ---- KALIBRACJA (na scenariuszu A, rate=100), z NOWA (v3) metoda referencji ----
print("=== KALIBRACJA v3 (self-excluding buffer) na scenariuszu A rate=100 ===")
target_fpr_per_measure = 0.025
thresholds = {}
for name, window, step in SCALES:
    # kalibrujemy prog iteracyjnie: zaczynamy od hojnego progu (bez wykluczania),
    # potem szacujemy kwantyl z-score przy tym progu - uproszczenie: uzywamy
    # tego samego 2-etapowego podejscia co w v2 (najpierw zbieramy z-score
    # bez samo-wykluczania jako przyblizenie startowe progu)
    all_z_pe, all_z_cv = [], []
    for seed in range(100, 130):
        rate = positions_to_rate_series(scenario_A(seed))
        _, pe, cv = sliding_features(rate, window, step)
        z_pe, _, _ = sequential_self_excluding_z(pe, thr=1e9)  # prog=inf -> nic nie wykluczamy, czysta kalibracja
        z_cv, _, _ = sequential_self_excluding_z(cv, thr=1e9)
        all_z_pe.extend(z_pe[~np.isnan(z_pe)])
        all_z_cv.extend(z_cv[~np.isnan(z_cv)])
    thr_pe = np.quantile(all_z_pe, 1 - target_fpr_per_measure)
    thr_cv = np.quantile(all_z_cv, 1 - target_fpr_per_measure)
    thresholds[(name, "PE")] = thr_pe
    thresholds[(name, "CV")] = thr_cv
    print(f"  skala {name}: prog PE={thr_pe:.3f}, prog CV={thr_cv:.3f}")

print("\n=== R2: FPR na NIEZALEZNYM zbiorze testowym, TEN SAM rezim (rate=100) ===")
for name, window, step in SCALES:
    fprs = []
    for seed in range(300, 320):
        flags, _ = detect_v3(scenario_A(seed), thresholds)
        fprs.append(np.mean(flags[name]))
    print(f"  skala {name}: FPR={np.mean(fprs):.3f} (cel: ~0.05)")

print("\n=== KLUCZOWY TEST #1 (v2): FPR przy INNYM tle (rate=60) ===")
for name, window, step in SCALES:
    fprs = []
    for seed in range(400, 420):
        flags, _ = detect_v3(scenario_A(seed, rate_scale=60.0), thresholds)
        fprs.append(np.mean(flags[name]))
    print(f"  skala {name}: FPR={np.mean(fprs):.3f} (v1: 0.621, v2: 0.033/0.095)")

print("\n=== KLUCZOWY TEST v3: wykrywanie B (klaster) i C (okresowy), + zdrowie bufora ===")
for label, fn in [("B) klaster", scenario_B), ("C) okresowy", scenario_C)]:
    det_short, det_long, health_short, health_long = [], [], [], []
    for seed in range(500, 515):
        flags, health = detect_v3(fn(seed), thresholds)
        det_short.append(np.mean(flags["KROTKA"]))
        det_long.append(np.mean(flags["DLUGA"]))
        health_short.append(health["KROTKA"])
        health_long.append(health["DLUGA"])
    print(f"  {label}: KROTKA={np.mean(det_short):.3f} (v1:0.899, v2:0.057), "
          f"DLUGA={np.mean(det_long):.3f} (v1:-, v2:0.066)")
    print(f"    zdrowie bufora KROTKA (frac pelny, PE/CV): {np.mean([h[0] for h in health_short]):.2f}/{np.mean([h[1] for h in health_short]):.2f}")
