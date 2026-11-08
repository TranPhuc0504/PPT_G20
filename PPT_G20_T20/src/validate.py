"""Buoc 4 (De tai 20): KIEM CHUNG tren ham co nghiem dung biet truoc.

  y = 1 + t tren [0,1]:  I(T) = T + T^2/2,  T* = -1 + sqrt(1 + 2Q)  (0 < Q < 1.5)
  Bao sai so nghiem |T - T*| va residual |I(T) - Q|; bang MAE, RMSE, E_inf theo dung sai.
  Hinh thang chinh xac cho ham tuyen tinh -> sai so chi con do dung sai chia doi va lam tron float64.
  (Bac hoi tu p thuc nghiem tren du lieu A/B do trong experiments.py.)

Dau ra (results/): verify_linear.csv, verify_linear_summary.csv
"""
import csv
import math

import numpy as np

from bisection import bisect
from common import DTYPE, load_config, results_dir
from integrate import cumulative


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


def main():
    cfg = load_config()
    res = [level1_linear(cfg)]
    print("\nKET QUA KIEM CHUNG: %s" % ("TAT CA DAT" if all(res) else "CO MUC CHUA DAT -> xem tren"))
    print("Ghi chu: tren y = 1 + t hinh thang chinh xac nen sai so chi do dung sai chia doi va lam tron;")
    print("         bac hoi tu p do tren du lieu A/B (lam thua luoi) trong experiments.py.")


if __name__ == "__main__":
    main()
