"""
Operator defektu v4 - architektura wielomodulowa (propozycja
uzytkownika): OSOBNY detektor zmiany rezimu, OSOBNY detektor
punktowych anomalii/struktury, fuzja decyzji zamiast jednej linii
bazowej robiacej wszystko.

DIAGNOZA Z v2/v3 (przypomnienie): jeden mechanizm (referencja
kroczaca) nie moze jednoczesnie (a) szybko dostosowac sie do
PRAWDZIWEJ zmiany rezimu tla, i (b) NIE dac sie "zatruc" czestym,
prawdziwym defektem. v2 wybieral (a) kosztem (b); v3 probowal (b)
kosztem (a).

ARCHITEKTURA v4:
  MODUL 1 - Detektor zmiany rezimu: dziala na DLUGICH blokach (znacznie
    dluzszych niz typowy defekt), porownuje mediane CV kolejnych blokow
    formalnym testem. Wykrywa TYLKO trwale przesuniecia calego tla, nie
    pojedyncze defekty (ktore sa krotkie wzgledem bloku).
  MODUL 2 - Detektor punktowych anomalii/struktury: dokladnie ten sam co
    w v1/v2 (entropia permutacyjna + CV, 2 skale okna), ale referencja
    jest ZAMROZONA na czas trwania biezacego rezimu - NIE aktualizuje
    sie oknem po oknie (unika "zatrucia" przez czesty defekt z v2), i
    aktualizuje sie TYLKO gdy Modul 1 potwierdzi prawdziwa zmiane rezimu
    (unika "zamrozenia na zawsze" z v3).
  FUZJA: decyzje z Modulu 1 (zmiana rezimu) i Modulu 2 (punktowa
    anomalia) sa ROZDZIELONE - zmiana rezimu NIE jest raportowana jako
    "defekt", tylko jako zdarzenie resetujace referencje Modulu 2.

TEST: (1) stabilny rezim (bazowy FPR), (2) PRAWDZIWA zmiana rezimu
w POLOWIE jednego przebiegu (rate 100->60) - sprawdza, czy FPR po
zmianie wraca do normy (naprawa problemu v3), (3) czeste defekty
klastrowe w stabilnym rezimie (sprawdza, czy wykrywanie nie zapada sie
jak w v2), (4) defekt okresowy (sprawdza, czy nadal wykrywany jak w v2/v3).
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

def positions_to_rate_series(positions, bin_width=20, total_len=None):
    if total_len is None:
        total_len = int(positions.max()) + 1000
    bins = np.arange(0, total_len, bin_width)
    counts, _ = np.histogram(positions, bins=bins)
    return counts.astype(float)

def scenario_stable(seed, rate_scale=100.0, n=2000):
    r = np.random.default_rng(seed)
    gaps = r.exponential(scale=rate_scale, size=n)
    return np.cumsum(gaps) + 1000

def scenario_regime_switch(seed, rate1=100.0, rate2=60.0, n_each=1000):
    r = np.random.default_rng(seed)
    gaps1 = r.exponential(scale=rate1, size=n_each)
    pos1 = np.cumsum(gaps1) + 1000
    gaps2 = r.exponential(scale=rate2, size=n_each)
    pos2 = pos1[-1] + np.cumsum(gaps2)
    return np.concatenate([pos1, pos2]), pos1[-1]

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

WINDOW, STEP, M = 60, 20, 4
BLOCK = 50          # okien na blok w Module 1 (znacznie dluzszy niz defekt)
REGIME_Z_THR = None # kalibrowane

def modul1_regime_change(cv_series, block=BLOCK, thr=None):
    """Porownuje mediane CV kolejnych blokow - formalny test zmiany
    rezimu na DLUGIEJ skali, odporny na krotkotrwale defekty."""
    n_blocks = len(cv_series) // block
    block_medians = [np.nanmedian(cv_series[i*block:(i+1)*block]) for i in range(n_blocks)]
    changes = []  # indeksy okien (w oryginalnej serii) gdzie wykryto zmiane
    for b in range(1, n_blocks):
        diff = abs(block_medians[b] - block_medians[b-1])
        if thr is not None and diff > thr:
            changes.append(b * block)
    return changes, block_medians

def modul2_point_anomaly(pe, cv, baseline_start, baseline_end, thr_pe, thr_cv):
    """Referencja ZAMROZONA - liczona raz z okien [baseline_start,
    baseline_end), uzywana dla WSZYSTKICH okien do nastepnej zmiany
    rezimu."""
    ref_pe = pe[baseline_start:baseline_end]
    ref_cv = cv[baseline_start:baseline_end]
    ref_pe = ref_pe[~np.isnan(ref_pe)]
    ref_cv = ref_cv[~np.isnan(ref_cv)]
    med_pe, mad_pe = np.median(ref_pe), np.median(np.abs(ref_pe - np.median(ref_pe)))
    med_cv, mad_cv = np.median(ref_cv), np.median(np.abs(ref_cv - np.median(ref_cv)))
    mad_pe = mad_pe if mad_pe > 1e-9 else 1e-9
    mad_cv = mad_cv if mad_cv > 1e-9 else 1e-9
    z_pe = np.abs(pe - med_pe) / (1.4826 * mad_pe)
    z_cv = np.abs(cv - med_cv) / (1.4826 * mad_cv)
    return (z_pe > thr_pe) | (z_cv > thr_cv)

def run_v4(positions, regime_thr, thr_pe, thr_cv, total_len=None):
    rate = positions_to_rate_series(positions, total_len=total_len)
    _, pe, cv = sliding_features(rate, WINDOW, STEP, M)
    changes, _ = modul1_regime_change(cv, BLOCK, regime_thr)
    # buduj segmenty rezimow na podstawie wykrytych zmian
    boundaries = [0] + changes + [len(pe)]
    flags = np.zeros(len(pe), dtype=bool)
    for i in range(len(boundaries) - 1):
        seg_start, seg_end = boundaries[i], boundaries[i+1]
        ref_end = min(seg_start + BLOCK, seg_end)  # kalibracja referencji z POCZATKU segmentu
        if ref_end - seg_start < 10:
            continue
        seg_flags = modul2_point_anomaly(pe[seg_start:seg_end], cv[seg_start:seg_end],
                                          0, ref_end - seg_start, thr_pe, thr_cv)
        flags[seg_start:seg_end] = seg_flags
    return flags, changes

# ---- KALIBRACJA ----
print("=== KALIBRACJA v4 (Modul 1: prog zmiany rezimu; Modul 2: progi PE/CV) na scenariuszu stabilnym rate=100 ===")
all_block_diffs, all_z_pe, all_z_cv = [], [], []
for seed in range(100, 130):
    positions = scenario_stable(seed)
    rate = positions_to_rate_series(positions, total_len=210000)
    _, pe, cv = sliding_features(rate, WINDOW, STEP, M)
    _, block_medians = modul1_regime_change(cv, BLOCK, thr=1e9)
    diffs = np.abs(np.diff(block_medians))
    all_block_diffs.extend(diffs[~np.isnan(diffs)])
    ref_pe, ref_cv = pe[:BLOCK], cv[:BLOCK]
    med_pe, mad_pe = np.median(ref_pe[~np.isnan(ref_pe)]), np.median(np.abs(ref_pe[~np.isnan(ref_pe)] - np.median(ref_pe[~np.isnan(ref_pe)])))
    med_cv, mad_cv = np.median(ref_cv[~np.isnan(ref_cv)]), np.median(np.abs(ref_cv[~np.isnan(ref_cv)] - np.median(ref_cv[~np.isnan(ref_cv)])))
    mad_pe = mad_pe if mad_pe > 1e-9 else 1e-9
    mad_cv = mad_cv if mad_cv > 1e-9 else 1e-9
    z_pe = np.abs(pe[BLOCK:] - med_pe) / (1.4826 * mad_pe)
    z_cv = np.abs(cv[BLOCK:] - med_cv) / (1.4826 * mad_cv)
    all_z_pe.extend(z_pe[~np.isnan(z_pe)])
    all_z_cv.extend(z_cv[~np.isnan(z_cv)])

regime_thr = np.quantile(all_block_diffs, 0.99)  # rzadkie zdarzenie w stabilnym rezimie
thr_pe = np.quantile(all_z_pe, 1 - 0.025)
thr_cv = np.quantile(all_z_cv, 1 - 0.025)
print(f"  prog zmiany rezimu (Modul 1): {regime_thr:.4f}")
print(f"  prog PE (Modul 2): {thr_pe:.3f}, prog CV (Modul 2): {thr_cv:.3f}")

# ---- TEST 1: stabilny rezim, niezalezne seedy (FPR bazowy) ----
print("\n=== TEST 1: FPR w stabilnym rezimie (rate=100), niezalezny zbior ===")
fprs = []
for seed in range(300, 320):
    positions = scenario_stable(seed)
    flags, changes = run_v4(positions, regime_thr, thr_pe, thr_cv, total_len=210000)
    fprs.append(np.mean(flags))
print(f"  FPR={np.mean(fprs):.3f} (cel: ~0.05)")

# ---- TEST 2: PRAWDZIWA zmiana rezimu w polowie przebiegu ----
print("\n=== TEST 2 (KLUCZOWY): FPR PO prawdziwej zmianie rezimu (rate 100->60 w polowie) ===")
fprs_before, fprs_after, n_changes_detected = [], [], []
for seed in range(400, 420):
    positions, switch_pos = scenario_regime_switch(seed)
    total_len = int(positions.max()) + 2000
    flags, changes = run_v4(positions, regime_thr, thr_pe, thr_cv, total_len=total_len)
    rate = positions_to_rate_series(positions, total_len=total_len)
    centers, _, _ = sliding_features(rate, WINDOW, STEP, M)
    switch_idx = np.searchsorted(centers, switch_pos / 20.0)  # FIX: centers sa w przestrzeni indeksow binow (bin_width=20), switch_pos w rzeczywistych jednostkach pozycji
    fprs_before.append(np.mean(flags[:switch_idx]))
    fprs_after.append(np.mean(flags[switch_idx + BLOCK:]))  # pomijamy okno przejsciowe rownej dlugosci co blok referencyjny
    n_changes_detected.append(len(changes) > 0)
print(f"  FPR PRZED zmiana (rate=100): {np.mean(fprs_before):.3f}")
print(f"  FPR PO zmianie (rate=60, po okresie przejsciowym): {np.mean(fprs_after):.3f} "
      f"(v1:0.621 caly czas, v2:0.033-0.095, v3:0.425-0.438 caly czas)")
print(f"  Modul 1 wykryl zmiane rezimu w {np.mean(n_changes_detected)*100:.0f}% przebiegow")

# ---- TEST 3: defekt klastrowy w STABILNYM rezimie ----
print("\n=== TEST 3: wykrywanie defektu B (klaster), stabilny rezim ===")
dets = []
for seed in range(500, 515):
    positions = scenario_B(seed)
    flags, changes = run_v4(positions, regime_thr, thr_pe, thr_cv, total_len=210000)
    dets.append(np.mean(flags))
print(f"  wykrywanie={np.mean(dets):.3f} (v1:0.899, v2:0.057, v3:0.673)")

# ---- TEST 4: defekt okresowy ----
print("\n=== TEST 4: wykrywanie defektu C (okresowy), stabilny rezim ===")
dets = []
for seed in range(500, 515):
    positions = scenario_C(seed)
    flags, changes = run_v4(positions, regime_thr, thr_pe, thr_cv, total_len=210000)
    dets.append(np.mean(flags))
print(f"  wykrywanie={np.mean(dets):.3f} (v1:0.002, v2:0.605, v3:0.739)")
