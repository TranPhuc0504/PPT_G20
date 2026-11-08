"""Buoc 3 (De tai 20): chia doi TU CAI DAT tim T sao cho F(T) = I(T) - Q = 0.

Quy tac (theo de):
  - khoang ban dau [t0, tN]; F(t0) = -Q < 0, F(tN) = tong - Q >= 0 (kiem tra truoc);
  - lap: m = (a+b)/2; neu F(m) >= 0 thi b = m (cap nhat can tren -> lay thoi diem SOM NHAT neu co doan phang)
         nguoc lai a = m;
  - dung khi do rong b - a <= tol (mac dinh 1e-6 phut) hoac het 100 vong;
  - bao residual |F(T)| (xe.phut) rieng voi sai so thoi diem (phut).

Dau ra khi chay rieng: results/bisection_results.csv (moi doan x luoi x thua x muc Q).
"""
import csv

from common import load_config, results_dir
from integrate import F_of_T, I_of_T, check_grid, cumulative, grid_path, q_levels, read_grid


def bisect(t, y, I, Q, tol, max_iter, F=None):
    """Tra ve dict: T, iters, width, residual, a, b. F tuy chon (de kiem chung ham khac)."""
    if F is None:
        def F(T):
            return F_of_T(t, y, I, Q, T)
    a, b = float(t[0]), float(t[-1])
    fa, fb = F(a), F(b)
    if fb < 0.0:
        raise ValueError("Q = %.6g lon hon tong tich phan %.6g: khong dat duoc" % (Q, fb + Q))
    if fa >= 0.0:                      # Q <= 0: dat ngay tai moc dau
        return {"T": a, "iters": 0, "width": 0.0, "residual": abs(fa), "a": a, "b": a}
    it = 0
    while (b - a) > tol and it < max_iter:
        m = (a + b) / 2.0
        if F(m) >= 0.0:
            b = m                      # cap nhat can tren khi F(m) >= 0
        else:
            a = m
        it += 1
    T = (a + b) / 2.0
    return {"T": T, "iters": it, "width": b - a, "residual": abs(F(T)), "a": a, "b": b}


def main():
    cfg = load_config()
    tol, mx = cfg["bisection"]["tol_minutes"], cfg["bisection"]["max_iter"]
    out = []
    for seg in cfg["segments"]:
        for kind in cfg["base_grids"]:
            Qs = None
            for f in cfg["thin_factors"]:
                t, y = read_grid(grid_path(seg, kind, f))
                check_grid(t, y)
                I = cumulative(t, y)
                if f == 1:
                    Qs = q_levels(float(I[-1]), cfg["q_fractions"])    # Q chot tu luoi goc
                for frac, Q in zip(cfg["q_fractions"], Qs):
                    r = bisect(t, y, I, Q, tol, mx)
                    out.append([seg, kind, "f%d" % f, "%d%%" % round(100 * frac), "%.9f" % Q,
                                "%.9f" % r["T"], r["iters"], "%.3e" % r["width"],
                                "%.3e" % r["residual"], "%.9f" % I_of_T(t, y, I, r["T"])])
    head = ["segment", "grid", "thin", "Q_phan_tram", "Q_xe_phut", "T_phut_tu_dau_doan",
            "so_vong", "do_rong_khoang_phut", "residual_xe_phut", "I(T)_xe_phut"]
    with open(results_dir() / "bisection_results.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(head)
        w.writerows(out)
    print("%-3s %-11s %-4s %-4s %12s %6s %12s" % ("Doan", "Luoi", "Thua", "Q", "T(phut)", "vong", "residual"))
    for r in out:
        print("%-3s %-11s %-4s %-4s %12s %6s %12s" % (r[0], r[1], r[2], r[3], r[5], r[6], r[8]))
    print("T tinh tu dau doan (phut). Residual don vi xe.phut; do rong khoang don vi phut.")
    print("LUU Y: nhan la prelabel -> ket qua SO BO.")


if __name__ == "__main__":
    main()
