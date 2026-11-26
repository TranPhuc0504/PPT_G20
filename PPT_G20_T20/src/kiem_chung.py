"""Kiểm chứng (Đề 20): chạy tích phân + chia đôi trên hàm biết trước đáp án y = 1 + t.

Chạy: python src\\kiem_chung.py
Ghi: results/verify_linear.csv (theo dung sai), results/verify_thin.csv (theo làm thưa lưới)
"""
import math

import numpy as np

from chuan_bi_du_lieu import lam_thua
from mo_hinh import DTYPE, bisect, bisect_diem_giua, cumulative, load_config, metrics, sci, write_csv


def T_dung(Q):
    # Đáp án chính xác: T* = -1 + sqrt(1 + 2Q), viết dạng 2Q / (1 + sqrt(1 + 2Q)) để tránh trừ hai số gần nhau
    # (nhân cả tử và mẫu với lượng liên hợp 1 + sqrt(1 + 2Q))
    return 2.0 * Q / (1.0 + math.sqrt(1.0 + 2.0 * Q))


def kiem_chung(cfg):
    v = cfg["verification"]
    n = v["n_intervals_linear"]                                   # số khoảng chia trên [0, 1]
    t = np.array([i / n for i in range(n + 1)], dtype=DTYPE)      # mốc 0, 0.1, ..., 1
    y = np.array([1.0 + x for x in t], dtype=DTYPE)               # y = 1 + t
    I = cumulative(t, y)                                          # hình thang: I[-1] phải đúng 1.5
    print("Hàm y = 1 + t trên [0, 1], %d khoảng | I_tot = %.15g (đúng = 1.5)" % (n, I[-1]))
    rows, dat = [], True
    for tol in v["tol_minutes_list"]:                             # từng mức dung sai
        errs = []
        for Q in v["q_values"]:                                   # Q = 0.375, 0.75, 1.125
            r = bisect(t, y, I, Q, tol, cfg["bisection"]["max_iter"])              # cách mới: T = b
            g = bisect_diem_giua(t, y, I, Q, tol, cfg["bisection"]["max_iter"])    # cách cũ: điểm giữa
            Te = T_dung(Q)
            e = r["T"] - Te                                       # sai số của T = b so với đáp án đúng
            errs.append(e)
            # Đạt: sai số <= tol/2 và tải tại T đã chạm Q (F(T) >= 0)
            dat = dat and abs(e) <= tol / 2 and r["residual"] >= 0
            rows.append(["%g" % tol, Q, "%.15f" % Te,
                         "%.15f" % r["T"], r["iters"], "%.3e" % abs(e), "%.3e" % r["residual"],
                         "%.15f" % g["T"], g["iters"], "%.3e" % abs(g["T"] - Te), "%.3e" % g["residual"],
                         "", "", ""])
        mae, rmse, einf = metrics(errs)
        rows.append(["%g" % tol, "tổng hợp (T = b)", "", "", "", "", "", "", "", "", "",   # dòng tổng hợp
                     "%.3e" % mae, "%.3e" % rmse, "%.3e" % einf])
        print("  tol = %-6g MAE = %s  RMSE = %s  E∞ = %s" % (tol, sci(mae), sci(rmse), sci(einf)))
    write_csv("verify_linear.csv",
              ["tol (phút)", "Q (xe·phút)", "T* đúng (phút)",
               "[Mới] T = b (phút)", "[Mới] Số vòng", "[Mới] |T − T*| (phút)", "[Mới] Residual F(T) (xe·phút)",
               "[Cũ] T = điểm giữa (phút)", "[Cũ] Số vòng", "[Cũ] |T − T*| (phút)", "[Cũ] Residual F(T) (xe·phút)",
               "MAE (phút)", "RMSE (phút)", "E∞ (phút)"], rows)
    print("KẾT QUẢ KIỂM CHỨNG: %s (|T − T*| <= tol/2 và F(T) >= 0 với mọi Q)" % ("ĐẠT" if dat else "KHÔNG ĐẠT"))
    print("Đã ghi results/verify_linear.csv")


def kiem_chung_lam_thua(cfg):
    # Làm thưa lưới kiểm chứng như Bước 5: f1, f2, f4, cùng hai đầu, cùng Q; so với đáp án đúng T*
    v = cfg["verification"]
    n = v["n_intervals_linear"]
    tol, mx = cfg["bisection"]["tol_minutes"], cfg["bisection"]["max_iter"]   # dung sai chính thức
    t = [i / n for i in range(n + 1)]
    y = [1.0 + x for x in t]
    print("\nLàm thưa lưới kiểm chứng (y = 1 + t, tol = %g), so với đáp án đúng T*" % tol)
    rows, E = [], {}
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
                         "%.3e" % r["residual"], "", "", "", ""])
        E[f] = metrics(errs)
        rows.append(["f%d" % f, len(tf), "tổng hợp", "", "", "", "",          # dòng tổng hợp của lưới
                     "%.3e" % E[f][0], "%.3e" % E[f][1], "%.3e" % E[f][2], ""])
        print("  f%d (%2d mốc): I_tot = %.15g  MAE = %s  RMSE = %s  E∞ = %s" % (
            f, len(tf), I[-1], sci(E[f][0]), sci(E[f][1]), sci(E[f][2])))
    p = math.log2(E[4][2] / E[2][2]) if E[2][2] > 0 and E[4][2] > 0 else float("nan")
    rows.append(["p = log2(E_f4/E_f2)", "", "", "", "", "", "", "", "", "", "%.3f" % p])
    write_csv("verify_thin.csv",
              ["Lưới", "Số mốc", "Q (xe·phút)", "T* đúng (phút)", "T = b (phút)", "|T − T*| (phút)",
               "Residual F(T) (xe·phút)", "MAE (phút)", "RMSE (phút)", "E∞ (phút)", "p"], rows)
    print("  p = log2(E_f4 / E_f2) = %.3f" % p)
    print("  => Sai số như nhau ở mọi lưới: hình thang chính xác với hàm bậc nhất, sai số chỉ do dung sai")
    print("     chia đôi, nên p = 0 (không phụ thuộc bước lưới). Bậc trên dữ liệu thật: xem mo_hinh.py.")
    print("Đã ghi results/verify_thin.csv")


if __name__ == "__main__":
    cfg = load_config()
    kiem_chung(cfg)
    kiem_chung_lam_thua(cfg)