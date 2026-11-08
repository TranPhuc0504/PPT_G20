"""Buoc 5 (De tai 20): do bien dong cua T do (1) LAM THUA LUOI va (2) DUNG SAI chia doi, tren du lieu A/B.

Quy uoc:
  - Q chot tu luoi goc f1 (25/50/75% tong), dung lai cho f2, f4 (de yeu cau: "cung Q da chot tu luoi goc").
  - Du lieu A/B KHONG co nghiem dung, nen lay ket qua tren luoi goc f1 (voi dung sai rat nho) lam MOC SO SANH.
    Do lech |T(f) - T(f1)| la anh huong cua lay mau, KHONG phai sai so so voi "su that".
  - (1) MAE / RMSE / E_inf cua do lech theo cac muc Q; p_thuc_nghiem = log2(E_f4 / E_f2) (chi la CHI BAO
        tren du lieu nhieu, vi f2, f4 la tap con cua luoi goc chu khong phai luoi chia doi muc thuc).
  - (2) Dung sai: T(tol) so voi T(tol rat nho = 1e-12) tren cung luoi f1; do lech phai <= tol.
  - So sanh hai loai bien dong: do lech do lay mau (phut) thuong LON HON NHIEU do lech do dung sai.

Dau ra (results/): sampling_effect.csv, sampling_summary.csv, tolerance_study.csv
"""
import csv
import math

from bisection import bisect
from common import load_config, results_dir
from integrate import check_grid, cumulative, grid_path, q_levels, read_grid
from validate import metrics, write_csv

REF_TOL = 1e-12


def main():
    cfg = load_config()
    mx = cfg["bisection"]["max_iter"]
    tol = cfg["bisection"]["tol_minutes"]
    rows, summ, tolrows = [], [], []

    for seg in cfg["segments"]:
        for kind in cfg["base_grids"]:
            data = {}
            for f in cfg["thin_factors"]:
                t, y = read_grid(grid_path(seg, kind, f))
                check_grid(t, y)
                data[f] = (t, y, cumulative(t, y))
            t1, y1, S1 = data[1]
            Qs = q_levels(float(S1[-1]), cfg["q_fractions"])

            # (1) anh huong cua lam thua luoi
            Tref = [bisect(t1, y1, S1, Q, REF_TOL, 200)["T"] for Q in Qs]
            dev = {}
            for f in cfg["thin_factors"]:
                if f == 1:
                    continue
                t, y, I = data[f]
                errs = []
                for frac, Q, Tr in zip(cfg["q_fractions"], Qs, Tref):
                    if Q > I[-1]:
                        rows.append([seg, kind, "f%d" % f, "%d%%" % round(100 * frac), "%.6f" % Q, "%.6f" % Tr,
                                     "", "", "Q lon hon tong tren luoi thua: khong dat duoc"])
                        errs = None
                        break
                    T = bisect(t, y, I, Q, tol, mx)["T"]
                    errs.append(T - Tr)
                    rows.append([seg, kind, "f%d" % f, "%d%%" % round(100 * frac), "%.6f" % Q, "%.6f" % Tr,
                                 "%.6f" % T, "%.6f" % (T - Tr), ""])
                dev[f] = errs
                if errs:
                    mae, rmse, einf = metrics(errs)
                    summ.append([seg, kind, "f%d" % f, len(t), "%.4f" % mae, "%.4f" % rmse, "%.4f" % einf, ""])
            # chi bao bac: p = log2(E_f4 / E_f2) khi du hai muc
            if 2 in dev and 4 in dev and dev[2] and dev[4]:
                e2 = metrics(dev[2])[2]
                e4 = metrics(dev[4])[2]
                p = math.log2(e4 / e2) if e2 > 0 and e4 > 0 else float("nan")
                summ.append([seg, kind, "chi_bao_p", "", "", "", "", "%.3f" % p])

            # (2) dung sai chia doi tren luoi goc f1
            for frac, Q, Tr in zip(cfg["q_fractions"], Qs, Tref):
                for tl in cfg["tol_study_minutes"]:
                    r = bisect(t1, y1, S1, Q, tl, mx)
                    tolrows.append([seg, kind, "%d%%" % round(100 * frac), "%g" % tl, r["iters"],
                                    "%.6f" % r["T"], "%.3e" % abs(r["T"] - Tr), "%.3e" % r["residual"]])

    write_csv("sampling_effect.csv", ["segment", "grid", "thin", "Q_phan_tram", "Q_xe_phut", "T_moc_f1_phut",
                                      "T_thua_phut", "T_thua-T_moc_phut", "ghi_chu"], rows)
    write_csv("sampling_summary.csv", ["segment", "grid", "thin", "n_moc", "MAE_phut", "RMSE_phut",
                                       "Einf_phut", "chi_bao_p"], summ)
    write_csv("tolerance_study.csv", ["segment", "grid", "Q_phan_tram", "tol_phut", "so_vong", "T_phut",
                                      "|T - T_chuan|_phut", "residual_xe_phut"], tolrows)

    print("(1) Anh huong LAM THUA luoi (so voi T tren luoi goc f1, phut)")
    print("%-3s %-11s %-9s %5s %9s %9s %9s %10s" % ("Doan", "Luoi", "Thua", "Moc", "MAE", "RMSE", "E_inf", "chi bao p"))
    for r in summ:
        print("%-3s %-11s %-9s %5s %9s %9s %9s %10s" % tuple(r))
    worst_tol = max(float(r[6]) for r in tolrows)
    off = [float(r[6]) for r in tolrows if float(r[3]) == tol]
    worst_off = max(off) if off else float("nan")
    worst_samp = max(float(r[6]) for r in summ if r[2] != "chi_bao_p")
    print("\n(2) Anh huong DUNG SAI chia doi (tren luoi goc), |T - T_chuan| lon nhat:")
    print("    - trong moi muc thu (%s): %.2e phut" % (", ".join("%g" % x for x in cfg["tol_study_minutes"]), worst_tol))
    print("    - tai dung sai chinh thuc %g: %.2e phut" % (tol, worst_off))
    print("\nSO SANH: E_inf do LAM THUA lon nhat = %.3f phut; bien dong do DUNG SAI chinh thuc = %.2e phut" % (
        worst_samp, worst_off))
    if worst_samp > 10 * worst_off:
        print("-> bien dong do lay mau/lam thua lon hon dung sai thuat toan it nhat 10 lan: sai so MO HINH/LAY MAU troi hon")
        print("   sai so toan hoc cua chia doi.")
    else:
        print("-> hai nguon bien dong cung bac: can xem them truoc khi ket luan.")
    print("Luu y: 'chi bao p' tren du lieu thuc rat nhieu (co the am hoac lech 2); bac p dang tin cay do tren y = 1 + t + t^2 (validate.py).")
    print("Nhan la prelabel -> moi ket qua SO BO.")

if __name__ == "__main__":
    main()
