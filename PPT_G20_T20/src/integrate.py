"""Buoc 1-2 (De tai 20): tich phan hinh thang TU CAI DAT, tong, Q va ham F(T).

Khong goi ham tich phan / noi suy cua thu vien. NumPy chi dung de luu mang float64.

Cong thuc (t tinh bang PHUT, y la so xe, tich phan la xe.phut):
  y~(t)  = noi suy tuyen tinh tung doan qua cac diem (t_i, y_i)
  I_k    = tich luy den t_k:  I_0 = 0,  I_{k+1} = I_k + h_k * (y_k + y_{k+1}) / 2
  I(T)   = I_k + y_k * s + m_k * s^2 / 2     (T thuoc [t_k, t_{k+1}], s = T - t_k, m_k = do doc)
  F(T)   = I(T) - Q                          (lien tuc, khong nhay bac theo chi so)

Dau ra khi chay rieng: results/integral_summary.csv (tong, thoi gian phu, trung binh, Q) cho moi doan/luoi.
"""
import csv

import numpy as np

from common import DTYPE, data_dir, load_config, results_dir


def as_f64(x):
    return np.asarray(x, dtype=DTYPE)


def check_grid(t, y):
    """Kiem tra dau vao: tang nghiem ngat, huu han, >= 2 moc, cung do dai."""
    if len(t) != len(y) or len(t) < 2:
        raise ValueError("can it nhat 2 moc va len(t) == len(y)")
    for i in range(len(t)):
        if not (t[i] == t[i]) or abs(t[i]) == float("inf") or not (y[i] == y[i]):
            raise ValueError("gia tri khong huu han tai moc %d" % i)
        if i > 0 and not t[i] > t[i - 1]:
            raise ValueError("thoi gian phai tang nghiem ngat (moc %d)" % i)


def cumulative(t, y):
    """Mang tich luy I_k (xe.phut) tai cac moc, tinh bang cong hinh thang."""
    n = len(t)
    I = np.zeros(n, dtype=DTYPE)
    for k in range(n - 1):
        h = t[k + 1] - t[k]
        I[k + 1] = I[k] + h * (y[k] + y[k + 1]) / 2.0
    return I


def locate(t, T):
    """Chi so k sao cho t[k] <= T <= t[k+1] (tim nhi phan thu cong). Kep T vao [t0, tN]."""
    n = len(t)
    if T <= t[0]:
        return 0
    if T >= t[n - 1]:
        return n - 2
    lo, hi = 0, n - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if t[mid] <= T:
            lo = mid
        else:
            hi = mid
    return lo


def y_interp(t, y, T):
    """y~(T): noi suy tuyen tinh tung doan."""
    k = locate(t, T)
    h = t[k + 1] - t[k]
    return y[k] + (y[k + 1] - y[k]) * (T - t[k]) / h


def I_of_T(t, y, I, T):
    """I(T) = I_k + y_k*s + m_k*s^2/2 : phan hinh thang cuoi ket thuc DUNG tai T."""
    k = locate(t, T)
    s = T - t[k]
    m = (y[k + 1] - y[k]) / (t[k + 1] - t[k])
    return I[k] + y[k] * s + m * s * s / 2.0


def F_of_T(t, y, I, Q, T):
    return I_of_T(t, y, I, T) - Q


def q_levels(total, fractions):
    return [f * total for f in fractions]


def read_grid(path):
    t, y = [], []
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            t.append(float(r["t_min"]))
            y.append(float(r["y"]))
    return as_f64(t), as_f64(y)


def grid_path(seg, kind, f):
    return data_dir() / ("grid_%s_%s_f%d.csv" % (seg, kind, f))


def main():
    cfg = load_config()
    rows = []
    for seg in cfg["segments"]:
        for kind in cfg["base_grids"]:
            Qs = None
            for f in cfg["thin_factors"]:
                t, y = read_grid(grid_path(seg, kind, f))
                check_grid(t, y)
                I = cumulative(t, y)
                total = float(I[-1])
                cover = float(t[-1] - t[0])
                if f == 1:
                    Qs = q_levels(total, cfg["q_fractions"])        # Q chot tu luoi goc f1
                rows.append([seg, kind, "f%d" % f, len(t), "%.9f" % cover, "%.9f" % total,
                             "%.9f" % (total / cover)] + ["%.9f" % q for q in Qs])
    head = ["segment", "grid", "thin", "n_moc", "thoi_gian_phu_phut", "tong_I_xe_phut",
            "trung_binh_xe"] + ["Q%d%%_xe_phut" % round(100 * q) for q in cfg["q_fractions"]]
    with open(results_dir() / "integral_summary.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(head)
        w.writerows(rows)
    print("%-3s %-11s %-4s %5s %10s %14s %10s" % ("Doan", "Luoi", "Thua", "Moc", "Phu(phut)", "I(xe.phut)", "TB(xe)"))
    for r in rows:
        print("%-3s %-11s %-4s %5s %10s %14s %10s" % tuple(r[:7]))
    print("Q (xe.phut) chot tu luoi goc f1; f2, f4 dung lai dung Q do.")
    print("LUU Y: nhan la prelabel -> ket qua SO BO.")


if __name__ == "__main__":
    main()
