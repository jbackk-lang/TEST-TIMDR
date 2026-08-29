"""
Test: czy pojedyncze trzesienie jest "rzadkim sygnalem" (pasuje do
zalozen architektury v4 z defect-operator), a roj wstrzasow wtornych
lamie to zalozenie tak samo jak scenariusz B (klaster) w
defect-operator?

METODA: STA/LTA (short-term/long-term average) - PRAWDZIWY, standardowy
algorytm sejsmologiczny (Allen, 1978), nie autorska metoda. Uzyty tu
zarowno jako test praktyczny, jak i niejawny test architektoniczny:
STA/LTA jest ILORAZEM, wiec z definicji powinien byc odporny na powolna
zmiane poziomu tla bez potrzeby osobnego "modulu zmiany rezimu" z v4 -
test to sprawdza empirycznie.

SCENARIUSZE:
  A) Tlo + powolna zmiana rezimu w polowie (np. sztorm, poziom x2)
  B) Tlo + jedno izolowane trzesienie (kontrola pozytywna, rzadki sygnal)
  C) Tlo + roj wstrzasow wtornych wg prawa Omoriego (test hipotezy:
     roj = scenariusz B/klaster z defect-operator)

Jeden przebieg, seed ustalony, wynik raportowany uczciwie - w tym
wynik C, ktory okazal sie bardziej niuansowany niz prosta hipoteza
"roj = catastrophic collapse jak w defect-operator".
"""
import numpy as np

N = 20000
STA_WIN, LTA_WIN = 20, 200


def sta_lta_ratio(energy, sta_win=STA_WIN, lta_win=LTA_WIN):
    cs = np.cumsum(np.insert(energy, 0, 0))

    def running_mean(win):
        out = np.full(len(energy), np.nan)
        for i in range(win, len(energy)):
            out[i] = (cs[i] - cs[i - win]) / win
        return out

    sta, lta = running_mean(sta_win), running_mean(lta_win)
    return sta / np.where(lta > 1e-9, lta, 1e-9), lta


def background(seed, regime_switch_at=None, level2_mult=2.0):
    r = np.random.default_rng(seed)
    amp = np.ones(N)
    if regime_switch_at is not None:
        amp[regime_switch_at:] *= level2_mult
    return amp * r.normal(0, 1, N)


def add_transient(raw, t0, amplitude, decay_tau=15.0, omega=1.5):
    t = np.arange(N) - t0
    mask = t >= 0
    transient = np.zeros(N)
    transient[mask] = amplitude * np.exp(-t[mask] / decay_tau) * np.sin(omega * t[mask])
    raw = raw.copy()
    raw[mask] += transient[mask]
    return raw


def omori_aftershock_times(t_mainshock, n_aftershocks, K=30.0, c=20.0, p=1.05, t_max=5000):
    """Czasy wstrzasow wtornych wg prawa Omoriego (rate ~ K/(t+c)^p),
    metoda odrzucania. c i K dobrane tak, by skala czasowa byla
    porownywalna z STA_WIN/LTA_WIN (udokumentowany wybor, nie ukryty)."""
    times = []
    t = 0.0
    lam_max = K / c ** p
    r = np.random.default_rng(999)
    while t < t_max and len(times) < n_aftershocks:
        t += r.exponential(1.0 / lam_max)
        if t >= t_max:
            break
        if r.uniform(0, lam_max) <= K / (t + c) ** p:
            times.append(t_mainshock + t)
    return times


if __name__ == "__main__":
    print("=== KALIBRACJA progu STA/LTA na czystym tle ===")
    ratios_calib = []
    for seed in range(100, 120):
        ratio, _ = sta_lta_ratio(background(seed) ** 2)
        ratios_calib.extend(ratio[~np.isnan(ratio)])
    threshold = np.quantile(ratios_calib, 1 - 0.02)
    print(f"  prog (FPR docelowy 2%): {threshold:.3f}")

    print("\n=== TEST A: FPR przy powolnej zmianie rezimu tla (x2 w polowie) ===")
    switch_at = N // 2
    fpr_before, fpr_after = [], []
    for seed in range(300, 320):
        ratio, _ = sta_lta_ratio(background(seed, regime_switch_at=switch_at) ** 2)
        fpr_before.append(np.nanmean(ratio[LTA_WIN:switch_at] > threshold))
        fpr_after.append(np.nanmean(ratio[switch_at + LTA_WIN:] > threshold))
    print(f"  FPR przed zmiana: {np.mean(fpr_before):.3f}, po zmianie: {np.mean(fpr_after):.3f} "
          f"(cel: oba ~0.02 - test naturalnej odpornosci ilorazu STA/LTA na regime shift, BEZ osobnego modulu)")

    print("\n=== TEST B: izolowane trzesienie (kontrola pozytywna) ===")
    detected, false_outside = [], []
    for seed in range(500, 520):
        eq_time = N // 2
        raw = add_transient(background(seed), eq_time, amplitude=4.0)
        ratio, _ = sta_lta_ratio(raw ** 2)
        detected.append(np.any(ratio[eq_time - 5:eq_time + 60] > threshold))
        outside = np.concatenate([ratio[LTA_WIN:eq_time - 5], ratio[eq_time + 60:]])
        false_outside.append(np.nanmean(outside > threshold))
    print(f"  wykrycie: {np.mean(detected) * 100:.0f}%, falszywy alarm poza oknem: {np.mean(false_outside):.3f}")

    print("\n=== TEST C: roj wstrzasow wtornych (Omori) - wplyw na wykrywalnosc POJEDYNCZYCH aftershockow ===")
    seed = 600
    t_ms = N // 3
    raw = add_transient(background(seed), t_ms, amplitude=5.0)
    aft_times = omori_aftershock_times(t_ms, 100, t_max=N - t_ms - 100)
    rng = np.random.default_rng(seed + 1)
    for at in aft_times:
        if at < N - 50:
            raw = add_transient(raw, int(round(at)), amplitude=rng.uniform(0.5, 2.5))
    ratio, lta = sta_lta_ratio(raw ** 2)

    hits = []
    for at in aft_times:
        idx = int(round(at))
        if idx + 30 >= N:
            continue
        window = ratio[max(0, idx - 2):idx + 30]
        rel = at - t_ms
        hits.append((rel, np.nanmax(window) > threshold if len(window) else False))
    early = [h for rel, h in hits if rel < 200]
    late = [h for rel, h in hits if rel >= 200]
    print(f"  wykrycie WCZESNYCH aftershockow (<200 probek od gl. wstrzasu, n={len(early)}): {np.mean(early) * 100:.0f}%")
    print(f"  wykrycie POZNYCH aftershockow (>=200 probek, n={len(late)}): {np.mean(late) * 100:.0f}%")
    print(f"  (dla porownania: izolowane trzesienie w tescie B: 100%)")
    print(f"  LTA: baseline={lta[t_ms-300]:.2f}, +50 od gl.wstrzasu={lta[t_ms+50]:.2f}, "
          f"+500 w roju={lta[t_ms+500]:.2f}, +1000 w roju={lta[t_ms+1000]:.2f} (baseline kalibracyjne ~1,0)")
