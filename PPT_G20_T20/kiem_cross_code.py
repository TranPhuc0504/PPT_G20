"""Kiểm mã chéo (Cross-code GĐ2): người KHÔNG viết code chạy lại gói từ đầu và lập biên bản.

Chạy (mở cmd tại thư mục gói PPT_G20_T20, nơi có main.py):
    python kiem_cross_code.py --nguoi-kiem "G20_SV02 Nguyen Van B"

Tool làm gì:
  1. Chép gói sang một thư mục tạm Ở CHỖ KHÁC (bỏ results/ cũ) -> kiểm được đường dẫn tương đối.
  2. Chạy python main.py trong bản chép, từ đầu.
  3. So từng bảng results/*.csv của bản chạy lại với results/ của nhóm: khớp 100% từng ký tự hay không
     (không khớp thì báo sai lệch số lớn nhất). Đếm hình PNG trong results/ (cần >= 2).
  4. Quét src/: không gọi hàm giải sẵn cho phần lõi (scipy.optimize, scipy.integrate, np.trapz, ...),
     không có đường dẫn tuyệt đối, có dùng float64; config.json có seed 2026.
  5. Ghi biên bản bien_ban_cross_code.md (kèm log chạy) vào thư mục gói.
Tool chỉ ghi lại những gì máy chạy ra; người kiểm đọc lại biên bản và ký xác nhận.
"""
import argparse
import csv
import datetime
import io
import json
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CAM = [r"scipy\.optimize", r"scipy\.integrate", r"\bbrentq\b", r"\bfsolve\b", r"\bnewton\(", r"np\.trapz",
       r"np\.trapezoid", r"cumulative_trapezoid", r"np\.interp\b", r"np\.linalg\.solve", r"np\.roots"]
CHO_PHEP = {"doi_chung_thu_vien.py"}   # file Level 2: được gọi thư viện, chỉ để so sánh, không phải phần lõi
TUYET_DOI = re.compile(r"[A-Za-z]:\\\\|[A-Za-z]:/|/home/|/Users/|/mnt/|/content/")


def doc_bang(p):
    return list(csv.reader(io.StringIO(p.read_text(encoding="utf-8-sig"))))


def lech_so(a, b):
    """Sai lệch số lớn nhất giữa hai bảng cùng kích thước; None nếu khác kích thước / khác chữ."""
    A, B = doc_bang(a), doc_bang(b)
    if len(A) != len(B) or any(len(x) != len(y) for x, y in zip(A, B)):
        return None, "khác số dòng/cột"
    m, chu = 0.0, 0
    for x, y in zip(A, B):
        for u, v in zip(x, y):
            if u == v:
                continue
            try:
                m = max(m, abs(float(u) - float(v)))
            except ValueError:
                chu += 1
    return m, ("%d ô chữ khác" % chu if chu else "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nguoi-kiem", required=True, dest="nguoi", help='ví dụ "G20_SV02 Nguyen Van B"')
    a = ap.parse_args()
    goc_kq = ROOT / "results"
    if not (ROOT / "main.py").exists() or not goc_kq.is_dir():
        sys.exit("Chạy tool trong thư mục gói (có main.py và results/ của nhóm).")
    cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    bang_goc = sorted(goc_kq.glob("*.csv"))

    tam = Path(tempfile.mkdtemp(prefix="cross_code_"))
    ban = tam / ROOT.name
    shutil.copytree(ROOT, ban, ignore=shutil.ignore_patterns("results", "figures", "__pycache__", "*.pyc", "bien_ban_cross_code*",
                                                             "*.zip", "cross_code_log.txt"))
    print("Chép gói sang %s và chạy main.py từ đầu..." % ban)
    t0 = datetime.datetime.now()
    r = subprocess.run([sys.executable, "main.py"], cwd=ban, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
    giay = (datetime.datetime.now() - t0).total_seconds()
    (ROOT / "cross_code_log.txt").write_text(r.stdout + "\n--- stderr ---\n" + r.stderr, encoding="utf-8")
    moi_kq = ban / "results"

    dong, khop = [], 0
    for p in bang_goc:
        q = moi_kq / p.name
        if not q.exists():
            dong.append((p.name, "KHÔNG ĐẠT", "bản chạy lại không tạo file này"))
            continue
        if p.read_bytes() == q.read_bytes() or p.read_text(encoding="utf-8-sig") == q.read_text(encoding="utf-8-sig"):
            dong.append((p.name, "ĐẠT", "khớp 100%"))
            khop += 1
        else:
            m, ghi = lech_so(p, q)
            dong.append((p.name, "KHÔNG ĐẠT", ghi if m is None else "lệch số lớn nhất %.3e %s" % (m, ghi)))
    them = sorted(x.name for x in moi_kq.glob("*.csv") if not (goc_kq / x.name).exists()) if moi_kq.is_dir() else []
    hinh_dir = ban / "results"
    hinh = sorted(x.name for x in hinh_dir.glob("*.png")) if hinh_dir.is_dir() else []

    cam, tuyet_doi, f64 = [], [], False
    for f in sorted((ban / "src").glob("*.py")) + [ban / "main.py"]:
        for k, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            code = line.split("#")[0]
            for pat in ([] if f.name in CHO_PHEP else CAM):
                if re.search(pat, code):
                    cam.append("%s:%d  %s" % (f.name, k, line.strip()))
            if TUYET_DOI.search(code):
                tuyet_doi.append("%s:%d  %s" % (f.name, k, line.strip()))
            f64 = f64 or "float64" in code
    seed_ok = int(cfg.get("seed", -1)) == 2026

    muc = [
        ("main.py chạy từ đầu không lỗi", r.returncode == 0, "mã thoát %d, %.0f giây" % (r.returncode, giay)),
        ("Tái lập 100% bảng CSV trong results/", khop == len(bang_goc) and len(bang_goc) > 0,
         "%d/%d bảng khớp" % (khop, len(bang_goc))),
        ("Có >= 2 đồ thị (results/)", len(hinh) >= 2, "%d hình: %s" % (len(hinh), ", ".join(hinh))),
        ("Không gọi hàm giải sẵn cho phần lõi", not cam, "%d chỗ nghi vấn (bỏ qua file đối chứng: %s)"
         % (len(cam), ", ".join(sorted(CHO_PHEP)))),
        ("Đường dẫn tương đối (chạy được ở thư mục khác)", not tuyet_doi and r.returncode == 0,
         "chạy tại %s; %d đường dẫn tuyệt đối" % (ban, len(tuyet_doi))),
        ("float64", f64 and cfg.get("dtype") == "float64", "config dtype = %s" % cfg.get("dtype")),
        ("Seed 2026 trong config.json", seed_ok, "seed = %s" % cfg.get("seed")),
    ]
    dat = all(x[1] for x in muc)
    L = ["# Biên bản kiểm mã chéo (Cross-code GĐ2) - Đề 20", "",
         "- Người kiểm: **%s**" % a.nguoi,
         "- Thời điểm chạy: %s" % t0.astimezone().isoformat(timespec="seconds"),
         "- Máy: %s | Python %s" % (platform.platform(), platform.python_version()),
         "- Gói kiểm: `%s` (chạy lại ở bản chép tạm `%s`)" % (ROOT.name, ban), "",
         "## Kết luận: %s" % ("ĐẠT - tái lập 100%" if dat else "CHƯA ĐẠT"), "",
         "| Hạng mục | Kết quả | Chi tiết |", "|---|---|---|"]
    L += ["| %s | %s | %s |" % (t, "ĐẠT" if ok else "KHÔNG ĐẠT", ct) for t, ok, ct in muc]
    L += ["", "## So sánh từng bảng", "", "| Bảng | Kết quả | Ghi chú |", "|---|---|---|"]
    L += ["| %s | %s | %s |" % x for x in dong]
    if them:
        L += ["", "Bảng chỉ có ở bản chạy lại (nhóm chưa nộp): " + ", ".join(them)]
    if cam:
        L += ["", "## Chỗ gọi hàm thư viện cần xem lại", ""] + ["- `%s`" % x for x in cam]
    if tuyet_doi:
        L += ["", "## Đường dẫn tuyệt đối", ""] + ["- `%s`" % x for x in tuyet_doi]
    L += ["", "Log chạy đầy đủ: `cross_code_log.txt`.", "",
          "Người kiểm xác nhận đã tự chạy và đọc biên bản: ...................................."]
    (ROOT / "bien_ban_cross_code.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    shutil.rmtree(tam, ignore_errors=True)
    for t, ok, ct in muc:
        print("  [%s] %s: %s" % ("ĐẠT" if ok else "KHÔNG ĐẠT", t, ct))
    print("\nKẾT LUẬN: %s. Biên bản: bien_ban_cross_code.md, log: cross_code_log.txt"
          % ("ĐẠT - tái lập 100%" if dat else "CHƯA ĐẠT"))
    if r.returncode != 0:
        print("main.py lỗi, xem cuối cross_code_log.txt:\n" + r.stderr[-1500:])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()