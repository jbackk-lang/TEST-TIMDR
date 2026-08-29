"""
PRE-REJESTRACJA: budowa i test NOWEGO kandydata na "operator defektu",
zastepujacego oba nieudane podejscia (transfer liczb pierwszych -
falszywy alarm na czystym szumie; torsja - matematycznie poprawna, ale
zbyt wrazliwa na szum przez wymog 3. pochodnej).

WYMAGANIA (ustalone PRZED projektowaniem operatora, zgodnie z prosba):
  R1. Klasa "brak defektu" musi byc jawnie zdefiniowana jako KONKRETNY
      rozklad referencyjny (nie "cokolwiek wyglada normalnie"), zbudowany
      z danych NIEZALEZNYCH od danych testowych.
  R2. Kontrola negatywna musi byc PRAWIDLOWA: prog flagowania kalibrowany
      na docelowy poziom istotnosci (np. 5% falszywych alarmow) na
      ZBIORZE WALIDACYJNYM oddzielonym od zbioru kalibracyjnego, i
      dodatkowo sprawdzony na INNYM typie sygnalu "bez defektu" (nie
      tylko dokladnie tym samym procesie co uzyto do kalibracji) - zeby
      wykryc, czy kalibracja jest wazna ogolnie, czy tylko dla jednego
      wariantu szumu.
  R3. Operator musi pokazac PRZEWAGE nad prostymi miarami juz
      przetestowanymi w tej sesji (CV lukow dla procesu radarowego,
      odleglosc od dopasowanej plaszczyzny dla trajektorii 3D) - albo
      wykrywajac to, czego one nie wykrywaja, albo dajac lepszy
      kontrast przy tym samym poziomie falszywych alarmow.

ZAMIANA "liczb pierwszych" NA COS ZAKOTWICZONEGO W SYGNALE:
  Zamiast importowac obca strukture matematyczna (rozklad odstepow
  miedzy liczbami pierwszymi), uzywamy entropii permutacyjnej
  (Bandt & Pompe 2002) - ugruntowanej, szeroko stosowanej miary
  STRUKTURY W PRZESTRZENI FAZOWEJ (wzorce porzadkowe m kolejnych
  probek), monitorowanej W OKNIE PRZESUWNYM wzgledem referencyjnego
  rozkladu z danych bez defektu - to jednoczesnie: (a) miara struktury
  w przestrzeni fazowej, (b) miara niestacjonarnosci/zmiany rozkladu
  (dryf entropii permutacyjnej wzgledem referencji), dokladnie jak
  zaproponowano.

ZASTOSOWANIE DO OBU WCZESNIEJSZYCH DOMEN (radar - proces punktowy,
IMU - trajektoria 3D) - test przenoszalnosci NOWEGO operatora, w
przeciwienstwie do transferu liczb pierwszych, ktory zawiodl.
"""
import numpy as np
from itertools import permutations
from math import log2

def permutation_entropy(x, m=4, tau=1):
    """Entropia permutacyjna Bandta-Pompe, znormalizowana do [0,1].
    Mierzy uporzadkowanie wzorcow rangowych dlugosci m w sygnale x -
    ugruntowana miara zlozonosci/struktury w przestrzeni fazowej,
    uzywana m.in. w diagnostyce uszkodzen mechanicznych, EEG, sygnalach
    finansowych (Bandt & Pompe, Phys. Rev. Lett. 2002)."""
    n = len(x)
    L = n - (m - 1) * tau
    if L < 10:
        return np.nan
    perms = {p: 0 for p in permutations(range(m))}
    for i in range(L):
        window = x[i:i + m * tau:tau]
        pattern = tuple(np.argsort(window))
        perms[pattern] += 1
    counts = np.array(list(perms.values()), dtype=float)
    probs = counts[counts > 0] / counts.sum()
    H = -np.sum(probs * np.log2(probs))
    return H / log2(__import__("math").factorial(m))

def sliding_pe(x, window_size, step, m=4, tau=1):
    out = []
    centers = []
    for start in range(0, len(x) - window_size, step):
        seg = x[start:start + window_size]
        out.append(permutation_entropy(seg, m, tau))
        centers.append(start + window_size // 2)
    return np.array(centers), np.array(out)

rng = np.random.default_rng(2026)

# ============ CZESC A: PROCES RADAROWY (punktowy) ============
print("############ DOMENA 1: proces radarowy (punktowy) ############\n")

def positions_to_rate_series(positions, bin_width=20, total_len=200000):
    bins = np.arange(0, total_len, bin_width)
    counts, _ = np.histogram(positions, bins=bins)
    return counts.astype(float)

def scenario_A(seed):
    r = np.random.default_rng(seed)
    gaps = r.exponential(scale=100.0, size=2000)
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

WINDOW, STEP, M = 60, 20, 4

# R1: zbuduj referencje z WIELU NIEZALEZNYCH realizacji scenariusza A (kalibracja)
ref_pe_values = []
for seed in range(100, 130):
    rate = positions_to_rate_series(scenario_A(seed))
    _, pe = sliding_pe(rate, WINDOW, STEP, M)
    ref_pe_values.extend(pe[~np.isnan(pe)])
ref_pe_values = np.array(ref_pe_values)
ref_mean, ref_std = ref_pe_values.mean(), ref_pe_values.std()
print(f"[R1] Referencja 'brak defektu' (30 niezaleznych realizacji A): "
      f"srednia PE={ref_mean:.4f}, std={ref_std:.4f}, n_probek={len(ref_pe_values)}")

# kalibracja progu na OSOBNYM zbiorze walidacyjnym (inne seedy niz referencja)
target_fpr = 0.05
calib_pe = []
for seed in range(200, 220):
    rate = positions_to_rate_series(scenario_A(seed))
    _, pe = sliding_pe(rate, WINDOW, STEP, M)
    calib_pe.extend(pe[~np.isnan(pe)])
calib_pe = np.array(calib_pe)
z_calib = np.abs((calib_pe - ref_mean) / ref_std)
threshold = np.quantile(z_calib, 1 - target_fpr)
print(f"[R2] Prog skalibrowany na NIEZALEZNYM zbiorze walidacyjnym A (seedy 200-219) "
      f"dla docelowego FPR={target_fpr}: prog_z={threshold:.3f}")
achieved_fpr = np.mean(z_calib > threshold)
print(f"     osiagniety FPR na tym samym zbiorze (sanity check kalibracji): {achieved_fpr:.3f}")

# TEST NA INNYM ZBIORZE TESTOWYM tego samego procesu A (jeszcze inne seedy)
test_pe = []
for seed in range(300, 320):
    rate = positions_to_rate_series(scenario_A(seed))
    _, pe = sliding_pe(rate, WINDOW, STEP, M)
    test_pe.extend(pe[~np.isnan(pe)])
test_pe = np.array(test_pe)
z_test = np.abs((test_pe - ref_mean) / ref_std)
fpr_test = np.mean(z_test > threshold)
print(f"[R2] FPR na NOWYM, niezaleznym zbiorze testowym A (seedy 300-319): {fpr_test:.3f} "
      f"(cel: ~{target_fpr})")

# R2 (mocniejszy test): FPR na INNYM RODZAJU szumu "bez defektu" - Poisson o innej intensywnosci
def scenario_A_other_rate(seed):
    r = np.random.default_rng(seed)
    gaps = r.exponential(scale=60.0, size=2000)  # inna intensywnosc niz referencja (100)
    return np.cumsum(gaps) + 1000

other_null_pe = []
for seed in range(400, 420):
    rate = positions_to_rate_series(scenario_A_other_rate(seed))
    _, pe = sliding_pe(rate, WINDOW, STEP, M)
    other_null_pe.extend(pe[~np.isnan(pe)])
other_null_pe = np.array(other_null_pe)
z_other = np.abs((other_null_pe - ref_mean) / ref_std)
fpr_other = np.mean(z_other > threshold)
print(f"[R2, mocniejszy test] FPR na INNYM procesie 'bez defektu' (Poisson, inna "
      f"intensywnosc, seedy 400-419): {fpr_other:.3f} (jesli >> {target_fpr}, "
      f"kalibracja NIE generalizuje)")

# R3: wykrywanie defektow B i C, porownanie z CV (najlepszy baseline z poprzedniego testu)
print()
for name, scenario_fn in [("B) klaster", scenario_B), ("C) okresowy", scenario_C)]:
    det_rates = []
    for seed in range(500, 510):
        positions = scenario_fn(seed)
        rate = positions_to_rate_series(positions)
        _, pe = sliding_pe(rate, WINDOW, STEP, M)
        z = np.abs((pe - ref_mean) / ref_std)
        det_rates.append(np.mean(z > threshold))
    print(f"[R3] Scenariusz {name}: sredni odsetek OKIEN oznaczonych jako defekt = "
          f"{np.mean(det_rates):.3f} (przy FPR kalibrowanym na {target_fpr} dla czystego szumu)")
