"""
PRE-REJESTRACJA: test poprawionej definicji torsji TIMDR, przesłanej
jako uzupełnienie wcześniejszego, nieformalnego diagramu:

    T(t) = [(x'(t) x x''(t)) . x'''(t)] / ||x'(t) x x''(t)||^2

(uzupełniono brakującą w transkrypcji trzecią pochodną x'''(t) — to
jest standardowy wzór skręcenia Freneta-Serreta dla krzywej w R^3,
założenie jawnie odnotowane; oryginalna wiadomość pokazywała
"(x'xx'').(t)" bez jasnego "x'''").

WAŻNE OGRANICZENIE (przyznane wprost przez autora — "sygnały
wielowymiarowe np. IMU"): iloczyn wektorowy x' x x'' wymaga wektorów
3D. Operator NIE jest zdefiniowany dla dowolnego SKALARNEGO sygnału
x(t) (np. jeden kanał radaru) bez wcześniejszego osadzenia w
przestrzeni fazowej (embedding Takensa). Ten test dotyczy przypadku,
dla którego wzór faktycznie ma sens: trajektoria 3D (IMU/mechanika).

TESTY:
  1. Helisa — znana analitycznie kappa=a/(a^2+b^2), tau=b/(a^2+b^2).
     Podstawowy sanity check poprawności implementacji wzoru.
  2. Linia prosta — x'xx''=0 wszędzie; warunek brzegowy użytkownika
     ("trajektoria nie jest liniowa") powinien to wyłapać.
  3. Elipsa płaska (z=0) — kappa!=0, ale tau=0 Z DEFINICJI (twierdzenie
     geometrii różniczkowej: krzywa płaska ma zerową torsję).
  4. Test defektu: płaska elipsa + realistyczny szum czujnika (IMU) +
     lokalnie wstrzyknięty "defekt skrętu" poza płaszczyzną. Porównanie
     z trywialnym baseline'em: odchylenie od globalnie dopasowanej
     płaszczyzny (PCA, bez żadnego różniczkowania).
  5. Skan parametrów (poziom szumu x szerokość wygładzania Savitzky-
     Golay) — żeby uczciwie sprawdzić, czy test 4 to pech dobranych
     parametrów, czy fundamentalne ograniczenie.

Pochodne liczone filtrem Savitzky-Golay (standardowa metoda numerycznego
różniczkowania zaszumionych sygnałów) — naiwne różnice skończone
wzmocniłyby szum jeszcze bardziej i dały nieuczciwie zaniżony wynik.
"""
import numpy as np
from scipy.signal import savgol_filter


def derivatives_3d(traj, dt, window=21, poly=5):
    v = np.zeros_like(traj)
    a = np.zeros_like(traj)
    j = np.zeros_like(traj)
    for k in range(3):
        v[:, k] = savgol_filter(traj[:, k], window, poly, deriv=1, delta=dt)
        a[:, k] = savgol_filter(traj[:, k], window, poly, deriv=2, delta=dt)
        j[:, k] = savgol_filter(traj[:, k], window, poly, deriv=3, delta=dt)
    return v, a, j


def curvature_torsion(v, a, j):
    cross = np.cross(v, a)
    cross_norm = np.linalg.norm(cross, axis=1)
    v_norm = np.linalg.norm(v, axis=1)
    kappa = np.divide(cross_norm, v_norm ** 3, out=np.full_like(cross_norm, np.nan), where=v_norm > 1e-9)
    denom = cross_norm ** 2
    numer = np.einsum('ij,ij->i', cross, j)
    tau = np.divide(numer, denom, out=np.full_like(numer, np.nan), where=denom > 1e-9)
    return kappa, tau, cross_norm


if __name__ == "__main__":
    print("=== TEST 1: Helisa (sanity check formuly) ===")
    a_h, b_h = 2.0, 0.5
    t = np.linspace(0, 8 * np.pi, 4000)
    dt = t[1] - t[0]
    traj = np.column_stack([a_h * np.cos(t), a_h * np.sin(t), b_h * t])
    v, acc, j = derivatives_3d(traj, dt)
    kappa, tau, _ = curvature_torsion(v, acc, j)
    mid = slice(200, -200)
    kappa_analytic = a_h / (a_h ** 2 + b_h ** 2)
    tau_analytic = b_h / (a_h ** 2 + b_h ** 2)
    print(f"  kappa: numeryczne={np.nanmean(kappa[mid]):.5f}  analityczne={kappa_analytic:.5f}")
    print(f"  tau:   numeryczne={np.nanmean(tau[mid]):.5f}  analityczne={tau_analytic:.5f}")

    print("\n=== TEST 2: Linia prosta (warunek brzegowy) ===")
    traj_line = np.column_stack([t, 2 * t, 3 * t])
    v2, acc2, j2 = derivatives_3d(traj_line, dt)
    cross_norm2 = np.linalg.norm(np.cross(v2, acc2), axis=1)
    print(f"  max ||x' x x''|| = {cross_norm2.max():.2e} (oczekiwane: ~0)")

    print("\n=== TEST 3: Elipsa plaska w z=0 (tau powinno = 0 z definicji) ===")
    traj_ellipse = np.column_stack([3 * np.cos(t), 1.5 * np.sin(t), np.zeros_like(t)])
    v3, acc3, j3 = derivatives_3d(traj_ellipse, dt)
    kappa3, tau3, _ = curvature_torsion(v3, acc3, j3)
    print(f"  kappa (!=0): {np.nanmean(kappa3[mid]):.5f}   tau (~0): max|tau|={np.nanmax(np.abs(tau3[mid])):.2e}")

    print("\n=== TEST 4: lokalny defekt skretu (elipsa + szum IMU + defekt) ===")
    rng = np.random.default_rng(7)
    traj_defect = np.column_stack([3 * np.cos(t), 1.5 * np.sin(t), np.zeros_like(t)]).copy()
    noise_sigma = 0.03
    traj_defect += rng.normal(0, noise_sigma, traj_defect.shape)
    defect_center, defect_width, defect_amp = 4 * np.pi, 0.5, 0.15
    defect_mask = np.abs(t - defect_center) < defect_width
    defect_signal = np.zeros_like(t)
    defect_signal[defect_mask] = defect_amp * np.sin(2 * np.pi * (t[defect_mask] - defect_center) / (2 * defect_width))
    traj_defect[:, 2] += defect_signal

    v4, acc4, j4 = derivatives_3d(traj_defect, dt)
    kappa4, tau4, _ = curvature_torsion(v4, acc4, j4)

    centroid = traj_defect.mean(axis=0)
    _, _, Vt = np.linalg.svd(traj_defect - centroid)
    plane_residual = np.abs((traj_defect - centroid) @ Vt[2])

    mid_mask = np.zeros_like(t, dtype=bool)
    mid_mask[200:-200] = True

    def report(signal, label):
        in_win = np.nanmean(np.abs(signal[defect_mask & mid_mask]))
        out_win = np.nanmean(np.abs(signal[mid_mask & ~defect_mask]))
        print(f"  {label}: okno={in_win:.4f}, tlo={out_win:.4f}, kontrast={in_win/out_win:.2f}x")

    report(tau4, "TORSJA tau(t)                ")
    report(kappa4 - np.nanmean(kappa4[mid_mask & ~defect_mask]), "KRZYWIZNA kappa(t) (bez tla)  ")
    report(plane_residual, "BASELINE odl. od plaszczyzny  ")

    print("\n=== TEST 5: skan szum x okno wygladzania ===")
    for noise_try, window_try in [(0.03, 21), (0.01, 21), (0.003, 21), (0.001, 21),
                                   (0.03, 51), (0.03, 101), (0.001, 51)]:
        traj_t = np.column_stack([3 * np.cos(t), 1.5 * np.sin(t), np.zeros_like(t)]).copy()
        rng2 = np.random.default_rng(7)
        traj_t += rng2.normal(0, noise_try, traj_t.shape)
        traj_t[:, 2] += defect_signal
        vv, aa, jj = derivatives_3d(traj_t, dt, window=window_try, poly=5)
        _, tt, _ = curvature_torsion(vv, aa, jj)
        in_win = np.nanmean(np.abs(tt[defect_mask & mid_mask]))
        out_win = np.nanmean(np.abs(tt[mid_mask & ~defect_mask]))
        print(f"  szum={noise_try:.4f}, okno={window_try}: tau_okno={in_win:.3f}, tau_tlo={out_win:.3f}, kontrast={in_win/out_win:.2f}x")
