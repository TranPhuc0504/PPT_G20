"""Kiểm chứng (Đề 20): chạy tích phân + chia đôi trên hàm biết trước đáp án y = 1 + t."""
import math

import numpy as np

from chuan_bi_du_lieu import lam_thua
from mo_hinh import DTYPE, bisect, cumulative, load_config, metrics, sci, write_csv


def T_dung(Q):
    # Đáp án chính xác: T* = -1 + sqrt(1 + 2Q), viết dạng T* = 2Q / (1 + sqrt(1 + 2Q)) để tránh trừ hai số gần nhau
    #                                           Nhân cả tử và mẫu với lượng liên hợp (1 + √(1+2Q))
    return 2.0 * Q / (1.0 + math.sqrt(1.0 + 2.0 * Q))


def kiem_chung(cfg):
    v = cfg["verification"]
    n = v["n_intervals_linear"]                                   # số khoảng chia trên [0, 1]
    t = np.array([i / n for i in range(n + 1)], dtype=DTYPE)      # mốc 0, 0.1, ..., 1
    y = np.array([1.0 + x for x in t], dtype=DTYPE)               # y = 1 + t
    I = cumulative(t, y)                                          # hình thang: I[-1] phải đúng 1.5
    print("Ham y = 1 + t tren [0, 1], %d khoang | I_tot = %.15g (dung = 1.5)" % (n, I[-1]))
    rows, summary, dat = [], [], True
    for tol in v["tol_minutes_list"]:                             # dung sai 1e-3, 1e-6 và 1e-9
        errs = []
        for Q in v["q_values"]:                                   # Q = 0.375, 0.75, 1.125
            r = bisect(t, y, I, Q, tol, cfg["bisection"]["max_iter"])
            Te = T_dung(Q)
            e = r["T"] - Te                                       # sai số so với đáp án đúng
            errs.append(e)
            dat = dat and abs(e) <= tol / 2                           # đạt nếu |T - T*| <= tol / 2
            rows.append(["%g" % tol, Q, "%.15f" % Te, "%.15f" % r["T"], "%.3e" % abs(e),
                         "%.3e" % r["residual"], r["iters"]])
        mae, rmse, einf = metrics(errs)
        summary.append(["%g" % tol, "%.3e" % mae, "%.3e" % rmse, "%.3e" % einf])
        print("  tol = %-6g MAE = %s  RMSE = %s  E_inf = %s" % (tol, sci(mae), sci(rmse), sci(einf)))
    write_csv("verify_linear.csv", ["tol_phut", "Q_xe_phut", "T_dung", "T_chia_doi", "|sai_so_T|_phut",
                                    "residual_xe_phut", "so_vong"], rows)
    write_csv("verify_linear_summary.csv", ["tol_phut", "MAE_phut", "RMSE_phut", "Einf_phut"], summary)
    print("KET QUA KIEM CHUNG: %s (|T - T*| <= tol / 2 voi moi Q)" % ("DAT" if dat else "KHONG DAT"))
    print("Da ghi results/verify_linear.csv va results/verify_linear_summary.csv")

def kiem_chung_lam_thua(cfg):
    # Làm thưa lưới kiểm chứng như Bước 5: f1, f2, f4, cùng hai đầu, cùng Q; so với đáp án đúng T*
    v = cfg["verification"]
    n = v["n_intervals_linear"]
    tol, mx = cfg["bisection"]["tol_minutes"], cfg["bisection"]["max_iter"]   # dung sai chính thức
    t = [i / n for i in range(n + 1)]
    y = [1.0 + x for x in t]
    print("\nLam thua luoi kiem chung (y = 1 + t, tol = %g), so voi dap an dung T*" % tol)
    rows, summary, E = [], [], {}
    for f in cfg["thin_factors"]:                                 # f1 (gốc), f2, f4
        tf, yf = lam_thua(t, y, f)                                # cùng quy tắc làm thưa với dữ liệu thật
        tf, yf = np.array(tf, dtype=DTYPE), np.array(yf, dtype=DTYPE)
        I = cumulative(tf, yf)
        errs = []
        for Q in v["q_values"]:
            r = bisect(tf, yf, I, Q, tol, mx)
            e = r["T"] - T_dung(Q)
            errs.append(e)
            rows.append(["f%d" % f, len(tf), Q, "%.15f" % T_dung(Q), "%.15f" % r["T"], "%.3e" % abs(e),
                         "%.3e" % r["residual"]])
        E[f] = metrics(errs)
        summary.append(["f%d" % f, len(tf), "%.15g" % I[-1], "%.3e" % E[f][0], "%.3e" % E[f][1],
                        "%.3e" % E[f][2], ""])
        print("  f%d (%2d moc): I_tot = %.15g  MAE = %s  RMSE = %s  E_inf = %s" % (
            f, len(tf), I[-1], sci(E[f][0]), sci(E[f][1]), sci(E[f][2])))
    p = math.log2(E[4][2] / E[2][2]) if E[2][2] > 0 and E[4][2] > 0 else float("nan")
    summary.append(["p = log2(E_f4/E_f2)", "", "", "", "", "", "%.3f" % p])
    write_csv("verify_thin.csv", ["luoi", "n_moc", "Q_xe_phut", "T_dung", "T_chia_doi", "|sai_so_T|_phut",
                                  "residual_xe_phut"], rows)
    write_csv("verify_thin_summary.csv", ["luoi", "n_moc", "I_tot", "MAE_phut", "RMSE_phut", "Einf_phut",
                                          "p"], summary)
    print("  p = log2(E_f4 / E_f2) = %.3f" % p)
    print("  => Sai so nhu nhau o moi luoi: hinh thang chinh xac voi ham bac nhat, sai so chi do dung sai")
    print("     chia doi, nen p = 0 (khong phu thuoc buoc luoi). Bac hoi tu tren du lieu that: xem mo_hinh.py.")
    print("Da ghi results/verify_thin.csv va results/verify_thin_summary.csv")

if __name__ == "__main__":
    cfg = load_config()
    kiem_chung(cfg)
    kiem_chung_lam_thua(cfg)