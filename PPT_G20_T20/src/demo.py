"""Demo tuong tac (De tai 20): nhap so tren man hinh, tim T bang chia doi, hien thi dang 10^-6.

Chay tu thu muc goc:   python src\\demo.py
Khong tinh toan lai gi moi: chi goi cumulative, bisect, exact_linear da co san.
"""
import math

from bisection import bisect
from common import load_config
from integrate import I_of_T, check_grid, cumulative, grid_path, locate, read_grid, y_interp
from validate import exact_linear


def sci(x, nd=3):
    """3.876e-13 -> '3.876 x 10^-13' (chi dung ky tu thuong, cmd nao cung hien duoc)."""
    if x == 0:
        return "0"
    m, e = ("%.*e" % (nd, x)).split("e")
    return "%s x 10^%d" % (m, int(e))


def hoi_so(msg, mac_dinh=None):
    while True:
        s = input(msg).strip()
        if s == "" and mac_dinh is not None:
            return mac_dinh
        try:
            return float(s)
        except ValueError:
            print("  Hay nhap mot so.")


def hoi_day(msg):
    while True:
        try:
            return [float(x) for x in input(msg).replace(",", " ").split()]
        except ValueError:
            print("  Chi nhap so, cach nhau boi dau cach.")


def hoi_tol():
    e = hoi_so("Dung sai tol = 10^? (Enter = -6): ", -6)
    return 10.0 ** e


def chay(t, y, Q, tol, max_iter):
    I = cumulative(t, y)
    r = bisect(t, y, I, Q, tol, max_iter)
    print("\n--- Ket qua ---")
    print("Tong I_tot       = %.9g xe.phut" % I[-1])
    print("Q                = %.9g xe.phut" % Q)
    print("T (chia doi)     = %.9f phut" % r["T"])
    print("So vong          = %d" % r["iters"])
    print("Do rong khoang   = %s phut   (<= tol = %s)" % (sci(r["width"]), sci(tol, 0)))
    print("Residual |F(T)|  = %s xe.phut" % sci(r["residual"]))
    print("I(T)             = %.9f xe.phut" % I_of_T(t, y, I, r["T"]))
    return r


def che_do_nhap_tay(cfg):
    print("\nNhap cac moc: t (phut, tang dan) va y (so xe), cung so phan tu.")
    t = hoi_day("t = ")
    y = hoi_day("y = ")
    try:
        check_grid(t, y)
    except ValueError as e:
        print("Loi dau vao:", e)
        return
    I = cumulative(t, y)
    q = hoi_so("q (0 < q <= 1, vi du 0.5) = ")
    if not (0 < q <= 1):
        print("q phai nam trong (0, 1].")
        return
    chay(t, y, q * I[-1], hoi_tol(), cfg["bisection"]["max_iter"])


def che_do_du_lieu(cfg):
    seg = input("Doan (A hoac B, Enter = A): ").strip().upper() or "A"
    kind = "timestamps"        # luoi goc chinh: timestamp that
    fs = cfg["thin_factors"]
    f = int(hoi_so("Muc lam thua f %s (f1 = luoi goc, Enter = 1): " % fs, 1))
    if f not in fs:
        print("f phai thuoc %s." % fs)
        return
    try:
        t, y = read_grid(grid_path(seg, kind, f))
        t1, y1 = read_grid(grid_path(seg, kind, 1))
    except OSError:
        print("Chua co file luoi. Chay truoc: python src\\data_prep.py")
        return
    check_grid(t, y)
    I = cumulative(t, y)
    tot_goc = float(cumulative(t1, y1)[-1])        # Q luon chot tu luoi goc f1
    n = len(t)
    print("\nDoan %s, luoi %s, f%d: %d moc (anh 0..%d), %d khoang (k = 0..%d)" % (seg, kind, f, n, n - 1, n - 1, n - 2))
    print("T tu %.4f den %.4f phut | I_tot = %.6f xe.phut" % (t[0], t[-1], I[-1]))
    if f != 1:
        print("(I_tot cua luoi goc f1 = %.6f; Q se tinh tu gia tri nay)" % tot_goc)
    while True:
        print("\n  a) Nhap T (phut)  -> tai tich luy I(T)")
        print("  b) Nhap k         -> thong tin khoang k")
        print("  c) Nhap q         -> tim T de I(T) = q * I_tot")
        print("  0) Quay lai")
        c = input("  Chon: ").strip().lower()
        if c == "a":
            T = hoi_so("  T = ")
            if not (t[0] <= T <= t[-1]):
                print("  T phai nam trong [%.4f, %.4f]." % (t[0], t[-1]))
                continue
            k = locate(t, T)
            print("  T nam trong khoang k = %d  (giua anh %d luc t = %.4f va anh %d luc t = %.4f)"
                  % (k, k, t[k], k + 1, t[k + 1]))
            print("  I_k = %.6f xe.phut, s = T - t_k = %.6f phut" % (I[k], T - t[k]))
            print("  y~(T) = %.6f xe" % y_interp(t, y, T))
            iT = I_of_T(t, y, I, T)
            print("  I(T)  = %.6f xe.phut  (%.2f%% tong)" % (iT, 100.0 * iT / I[-1]))
        elif c == "b":
            k = int(hoi_so("  k = "))
            if not (0 <= k <= n - 2):
                print("  k phai tu 0 den %d." % (n - 2))
                continue
            h = t[k + 1] - t[k]
            print("  Khoang k = %d: t tu %.4f den %.4f (h = %.4f phut)" % (k, t[k], t[k + 1], h))
            print("  y_k = %.4f, y_k+1 = %.4f (xe)" % (y[k], y[k + 1]))
            print("  Hinh thang A_k = h*(y_k + y_k+1)/2 = %.6f xe.phut" % (h * (y[k] + y[k + 1]) / 2.0))
            print("  I_k = %.6f, I_k+1 = %.6f xe.phut" % (I[k], I[k + 1]))
        elif c == "c":
            q = hoi_so("  q (0 < q <= 1, vi du 0.25) = ")
            if not (0 < q <= 1):
                print("  q phai nam trong (0, 1].")
                continue
            Q = q * tot_goc
            if Q > I[-1]:
                print("  Q = %.6f lon hon tong tren luoi f%d (%.6f): khong co nghiem." % (Q, f, I[-1]))
                continue
            r = chay(t, y, Q, hoi_tol(), cfg["bisection"]["max_iter"])
            print("T nam trong khoang k = %d" % locate(t, r["T"]))
        elif c == "0":
            break


def che_do_kiem_chung(cfg):
    n = cfg["verification"]["n_intervals_linear"]
    t = [i / n for i in range(n + 1)]
    y = [1.0 + x for x in t]
    print("\nHam y = 1 + t tren [0,1], I_tot = 1.5. Can 0 < Q < 1.5.")
    Q = hoi_so("Q = ")
    if not (0 < Q < 1.5):
        print("Q phai thoa 0 < Q < 1.5.")
        return
    tol = hoi_tol()
    r = chay(t, y, Q, tol, 200)
    Te = exact_linear(Q)
    print("T dung (giai tich) = %.12f phut   [T* = -1 + sqrt(1 + 2Q)]" % Te)
    e = abs(r["T"] - Te)
    print("Sai so nghiem |T - T*| = %s phut  -> %s" % (sci(e), "DAT" if e <= tol else "KHONG DAT"))


def main():
    cfg = load_config()
    while True:
        print("\n=== DEMO CHIA DOI (De 20) ===")
        print("1) Nhap tay cac moc t, y")
        print("2) Dung du lieu A/B (can chay data_prep.py truoc)")
        print("3) Kiem chung y = 1 + t (so voi nghiem giai tich)")
        print("0) Thoat")
        c = input("Chon: ").strip()
        if c == "1":
            che_do_nhap_tay(cfg)
        elif c == "2":
            che_do_du_lieu(cfg)
        elif c == "3":
            che_do_kiem_chung(cfg)
        elif c == "0":
            break


if __name__ == "__main__":
    main()
