"""Đề 20 - Thời điểm đạt chỉ số tải tích lũy: MỘT script chạy lại toàn bộ bảng và đồ thị.

Chạy (mở cmd tại thư mục gói, nơi có config.json):
    python main.py

Thứ tự (mỗi bước là một chương trình trong src/, gọi bằng đường dẫn tương đối):
    1. src/chuan_bi_du_lieu.py   đọc data/analysis_snapshot.csv, kiểm tra, tạo lưới đoạn A/B (f1, f2, f4)
    2. src/mo_hinh.py --het      tích phân hình thang + chia đôi, khảo sát làm thưa lưới và dung sai
    3. src/kiem_chung.py         kiểm chứng trên hàm y = 1 + t có nghiệm giải tích
    4. src/newton.py             phần mở rộng: Newton có bảo vệ, so với chia đôi
    4b. src/doi_chung_thu_vien.py Level 2: so code tự viết với numpy và scipy
    4c. src/doi_chieu_snapshot.py sai số dữ liệu: snapshot ban đầu vs sau nghiệm thu (chưa có file thì bỏ qua)
    5. src/ve_do_thi.py          vẽ đồ thị vào results/
    6. src/xuat_excel.py         gom bảng vào results/ket_qua_de20.xlsx (bỏ qua nếu thiếu openpyxl)

Seed: lấy từ config.json (mặc định 2026) và đặt cho random, numpy, PYTHONHASHSEED. Các thuật toán của đề
không dùng số ngẫu nhiên; seed được đặt để mọi lần chạy lại cho cùng kết quả.
Kiểu số: float64 (config.json: "dtype").
"""
import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUOC = [
    ("Chuẩn bị dữ liệu", ["src/chuan_bi_du_lieu.py"], True),
    ("Mô hình: tích phân + chia đôi + khảo sát", ["src/mo_hinh.py", "--het"], True),
    ("Kiểm chứng trên hàm y = 1 + t", ["src/kiem_chung.py"], True),
    ("Newton (mở rộng)", ["src/newton.py"], True),
    ("Đối chứng thư viện (Level 2)", ["src/doi_chung_thu_vien.py", "--het"], True),
    ("Sai số dữ liệu: đối chiếu snapshot", ["src/doi_chieu_snapshot.py"], True),
    ("Vẽ đồ thị", ["src/ve_do_thi.py"], True),
    ("Xuất Excel", ["src/xuat_excel.py"], False),          # không bắt buộc
]


def main():
    cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    seed = int(cfg.get("seed", 2026))
    if cfg.get("dtype", "float64") != "float64":
        sys.exit("config.json: dtype phải là float64.")
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
        ver_np = np.__version__
    except ImportError:
        sys.exit("Thiếu numpy. Cài: python -m pip install numpy matplotlib openpyxl scipy")
    env = dict(os.environ, PYTHONHASHSEED=str(seed), PYTHONIOENCODING="utf-8", MPLBACKEND="Agg")
    print("Đề 20 | seed = %d | dtype = float64 | Python %s | numpy %s"
          % (seed, sys.version.split()[0], ver_np))
    (ROOT / "results").mkdir(exist_ok=True)

    t0 = time.time()
    for i, (ten, lenh, bat_buoc) in enumerate(BUOC, 1):
        print("\n" + "=" * 70 + "\n[%d/%d] %s: python %s\n" % (i, len(BUOC), ten, " ".join(lenh)) + "=" * 70)
        if lenh[0].endswith("xuat_excel.py"):
            try:
                import openpyxl  # noqa: F401
            except ImportError:
                print("Bỏ qua: chưa cài openpyxl (không ảnh hưởng các bảng CSV và hình).")
                continue
        r = subprocess.run([sys.executable] + lenh, cwd=ROOT, env=env)
        if r.returncode != 0:
            if bat_buoc:
                sys.exit("\nDỪNG: bước %d (%s) lỗi, mã %d." % (i, ten, r.returncode))
            print("Cảnh báo: bước %d (%s) lỗi, bỏ qua vì không bắt buộc." % (i, ten))

    kq = sorted("results/" + p.name for p in (ROOT / "results").glob("*") if p.suffix in (".csv", ".xlsx", ".png"))
    print("\n" + "=" * 70)
    print("XONG sau %.1f giây: %d bảng CSV và %d hình PNG trong results/:" % (
        time.time() - t0, sum(n.endswith(".csv") for n in kq), sum(n.endswith(".png") for n in kq)))
    for n in kq:
        print("  " + n)


if __name__ == "__main__":
    main()