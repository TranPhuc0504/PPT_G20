"""Buoc 4 (De tai 20): KIEM CHUNG tren ham co nghiem dung biet truoc + doi chung thu vien.

Level 1 - ham giai tich:
  (a) y = 1 + t tren [0,1]:  I(T) = T + T^2/2,  T* = -1 + sqrt(1 + 2Q)  (0 < Q < 1.5)
      Hinh thang chinh xac cho ham tuyen tinh -> sai so chi con do dung sai chia doi va lam tron float64;
      => bac hoi tu p KHONG xac dinh tren ham nay.
  (b) y = 1 + t + t^2 tren [0,1]:  I(T) = T + T^2/2 + T^3/3 (ham tron, bo sung de do p).
      Luoi n khoang, h = 1/n; E_h = sai so thoi diem; p = log2(E_h / E_{h/2}) (ky vong ~ 2).
Level 2 - doi chung thu vien (NumPy/SciPy) tren du lieu A/B.
Level 3 - bang sai so MAE, RMSE, E_inf (tren cac muc Q).

Dau ra (results/): verify_linear.csv, verify_linear_summary.csv, verify_smooth.csv, verify_order.csv,
                   crosscheck_library.csv
"""
import csv
import math

import numpy as np

from bisection import bisect
from common import DTYPE, load_config, results_dir
from integrate import F_of_T, I_of_T, check_grid, cumulative, grid_path, q_levels, read_grid


def metrics(errs):
    n = len(errs)
    mae = sum(abs(e) for e in errs) / n
    rmse = math.sqrt(sum(e * e for e in errs) / n)
    einf = max(abs(e) for e in errs)
    return mae, rmse, einf


def write_csv(name, head, rows):
    with open(results_dir() / name, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(head)
        w.writerows(rows)


def exact_linear(Q):
    """T* = -1 + sqrt(1+2Q), viet dang on dinh 2Q/(1+sqrt(1+2Q)) de tranh tru hai so gan nhau."""
    return 2.0 * Q / (1.0 + math.sqrt(1.0 + 2.0 * Q))


def exact_smooth(Q):
    """Nghiem cua T + T^2/2 + T^3/3 = Q bang Newton tren da thuc (tham chieu)."""
    T = Q if Q < 1 else 1.0
    for _ in range(100):
        g = T + T * T / 2.0 + T ** 3 / 3.0 - Q
        dg = 1.0 + T + T * T                       # = y(T) > 0
        step = g / dg
        T -= step
        if abs(step) < 1e-17:
            break
    return T


def level1_linear(cfg):
    v = cfg["verification"]
    n = v["n_intervals_linear"]
    t = np.array([i / n for i in range(n + 1)], dtype=DTYPE)
    y = np.array([1.0 + x for x in t], dtype=DTYPE)
    I = cumulative(t, y)
    rows, summary, ok = [], [], True
    print("Level 1a: y = 1 + t tren [0,1]  (I(1) = %.15g)" % I[-1])
    for tol in v["tol_minutes_list"]:
        errs = []
        for Q in v["q_values"]:
            r = bisect(t, y, I, Q, tol, cfg["bisection"]["max_iter"])
            Te = exact_linear(Q)
            e = r["T"] - Te
            errs.append(e)
            rows.append(["%g" % tol, Q, "%.15f" % Te, "%.15f" % r["T"], "%.3e" % abs(e),
                         "%.3e" % r["residual"], r["iters"]])
            ok &= abs(e) <= tol                                    # sai so thoi diem phai <= dung sai
        mae, rmse, einf = metrics(errs)
        summary.append(["%g" % tol, "%.3e" % mae, "%.3e" % rmse, "%.3e" % einf])
        print("  tol=%g : MAE=%.2e  RMSE=%.2e  E_inf=%.2e" % (tol, mae, rmse, einf))
    write_csv("verify_linear.csv", ["tol_phut", "Q_xe_phut", "T_dung", "T_chia_doi", "|sai_so_T|_phut",
                                    "residual_xe_phut", "so_vong"], rows)
    write_csv("verify_linear_summary.csv", ["tol_phut", "MAE_phut", "RMSE_phut", "Einf_phut"], summary)
    print("  => %s (|T - T*| <= tol voi moi Q)" % ("DAT" if ok else "KHONG DAT"))
    return ok


def level1_smooth(cfg):
    v = cfg["verification"]
    tol = v["smooth_tol_minutes"]
    rows, per_n = [], []
    print("Level 1b: y = 1 + t + t^2 tren [0,1]  (do bac hoi tu p)")
    for n in v["smooth_n_list"]:
        t = np.array([i / n for i in range(n + 1)], dtype=DTYPE)
        y = np.array([1.0 + x + x * x for x in t], dtype=DTYPE)
        I = cumulative(t, y)
        errs = []
        for Q in v["smooth_q_values"]:
            r = bisect(t, y, I, Q, tol, 200)
            Te = exact_smooth(Q)
            e = r["T"] - Te
            errs.append(e)
            rows.append([n, "%.6f" % (1.0 / n), Q, "%.15f" % Te, "%.15f" % r["T"], "%.3e" % abs(e)])
        per_n.append((n,) + metrics(errs))
    write_csv("verify_smooth.csv", ["n_khoang", "h_phut", "Q_xe_phut", "T_dung", "T_h", "|sai_so_T|_phut"], rows)
    order = []
    for k, (n, mae, rmse, einf) in enumerate(per_n):
        if k + 1 < len(per_n):
            _, mae2, rmse2, einf2 = per_n[k + 1]
            p = [math.log2(a / b) for a, b in ((mae, mae2), (rmse, rmse2), (einf, einf2))]
            order.append([n, "%.3e" % mae, "%.3e" % rmse, "%.3e" % einf, "%.3f" % p[0], "%.3f" % p[1], "%.3f" % p[2]])
        else:
            order.append([n, "%.3e" % mae, "%.3e" % rmse, "%.3e" % einf, "", "", ""])
    write_csv("verify_order.csv", ["n_khoang", "MAE", "RMSE", "Einf", "p_MAE", "p_RMSE", "p_Einf"], order)
    print("  %6s %10s %10s %10s %7s %7s %7s" % ("n", "MAE", "RMSE", "E_inf", "p_MAE", "p_RMSE", "p_Einf"))
    for r in order:
        print("  %6s %10s %10s %10s %7s %7s %7s" % tuple(r))
    last = [r for r in order if r[6] != ""][-1]
    ok = all(abs(float(x) - 2.0) < 0.2 for x in last[4:7])
    print("  => p ~ 2 (hinh thang bac 2): %s" % ("DAT" if ok else "KIEM TRA LAI"))
    return ok


def level2_library(cfg):
    """Doi chung voi NumPy/SciPy: tong hinh thang va nghiem T tren cac luoi A/B."""
    try:
        from scipy.optimize import brentq
    except ImportError:
        print("Level 2: khong co SciPy, bo qua doi chung nghiem (pip install scipy)")
        brentq = None
    rows, worst_I, worst_T = [], 0.0, 0.0
    for seg in cfg["segments"]:
        for kind in cfg["base_grids"]:
            Qs = None
            for f in cfg["thin_factors"]:
                t, y = read_grid(grid_path(seg, kind, f))
                check_grid(t, y)
                I = cumulative(t, y)
                tot_lib = float(np.trapezoid(y, t))
                dI = abs(float(I[-1]) - tot_lib)
                worst_I = max(worst_I, dI)
                if f == 1:
                    Qs = q_levels(float(I[-1]), cfg["q_fractions"])
                for frac, Q in zip(cfg["q_fractions"], Qs):
                    if Q > I[-1]:
                        rows.append([seg, kind, "f%d" % f, "%d%%" % round(100 * frac), "%.9f" % Q, "", "", "",
                                     "Q > tong tren luoi nay"])
                        continue
                    r = bisect(t, y, I, Q, cfg["bisection"]["tol_minutes"], cfg["bisection"]["max_iter"])
                    Tlib = ""
                    dT = ""
                    if brentq is not None:
                        def Flib(T, t=t, y=y, Q=Q):
                            m = t < T
                            tt = np.append(t[m], T)
                            return float(np.trapezoid(np.interp(tt, t, y), tt)) - Q
                        Tl = brentq(Flib, float(t[0]), float(t[-1]), xtol=1e-12)
                        Tlib = "%.9f" % Tl
                        d = abs(r["T"] - Tl)
                        dT = "%.3e" % d
                        worst_T = max(worst_T, d)
                    rows.append([seg, kind, "f%d" % f, "%d%%" % round(100 * frac), "%.9f" % Q,
                                 "%.9f" % r["T"], Tlib, dT, ""])
    write_csv("crosscheck_library.csv", ["segment", "grid", "thin", "Q_phan_tram", "Q_xe_phut", "T_tu_cai",
                                         "T_scipy_brentq", "|chenh_lech|_phut", "ghi_chu"], rows)
    print("Level 2: so voi NumPy/SciPy tren %d to hop doan/luoi/thua/Q" % len(rows))
    print("  tong hinh thang: chenh lech lon nhat = %.2e xe.phut" % worst_I)
    print("  nghiem T       : chenh lech lon nhat = %.2e phut (dung sai chia doi %g)" % (
        worst_T, cfg["bisection"]["tol_minutes"]))
    return worst_I < 1e-6 and worst_T <= cfg["bisection"]["tol_minutes"] * 2


def main():
    cfg = load_config()
    res = [level1_linear(cfg), level1_smooth(cfg), level2_library(cfg)]
    print("\nKET QUA KIEM CHUNG: %s" % ("TAT CA DAT" if all(res) else "CO MUC CHUA DAT -> xem tren"))
    print("Ghi chu: tren y = 1 + t hinh thang chinh xac nen p khong xac dinh; p do tren y = 1 + t + t^2.")


if __name__ == "__main__":
    main()
