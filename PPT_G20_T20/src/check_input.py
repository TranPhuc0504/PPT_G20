"""Buoc 00: KIEM TRA DAU VAO truoc khi chay (Quy dinh muc 2.1 va 2.3).

Chay rieng:  python src/check_input.py            (hoac tu dong qua run_all.py)
Tuy chon:    python src/check_input.py --root <thu muc goc goi Traffic_BTL>   (kiem tra them file/anh theo goi)

Kiem tra:
  1. Du file cua goi Phan 2 (config.json, snapshot, cac script trong src/).
  2. Snapshot co du cot theo schema (Quy dinh 2.2); image_id la SHA256 (64 ky tu hex).
  3. timestamp la ISO 8601 co +07:00 va co giay; time_source hop le.
  4. label_status chi thuoc {human_verified, unreviewed_prelabel}; KHONG tron trong mot doan; label_version thong nhat.
  5. total_count = tong 4 lop (2wheel + bus + car + truck).
  6. Trung image_id, trung camera/timestamp -> ghi vao results/removed_records.csv (DANH SACH LOAI; rong neu khong co).
  7. Doi chieu ten recording_id (co ngay) voi ngay cua timestamp.
  8. Hai doan A/B: moi doan 1 camera + 1 recording, 80-300 quan sat; hai doan khac recording va khong giao nhau theo thoi gian.
  9. (voi --root) file README/classes/roi, anh trong image_path co that.

Khong tu tao anh, nhan, timestamp de lap cho thieu (Quy dinh 2.1). Muc ERROR -> thoat voi ma loi 1.
Dau ra: results/input_check.csv, results/removed_records.csv
"""
import argparse
import csv
import re
import sys
from pathlib import Path

import pandas as pd

from common import ROOT, load_config, results_dir

SCHEMA = ["image_id", "image_path", "camera_id", "recording_id", "timestamp", "time_source", "label_status",
          "label_version", "count_2wheel", "count_bus", "count_car", "count_truck", "total_count", "roi_id",
          "view_id", "roi_version", "roi_valid", "roi_vehicle_count", "roi_occupancy", "is_resampled",
          "source_image_ids", "analysis_segment"]
LABEL_OK = {"human_verified", "unreviewed_prelabel"}
TIME_SOURCES = {"source_metadata", "filename", "manifest"}
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?\+07:00$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")

REPORT = []


def add(check, value, level):
    REPORT.append((check, value, level))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="", help="thu muc goc goi Traffic_BTL (de kiem tra shared/ va anh)")
    a, _ = ap.parse_known_args()
    cfg = load_config()

    # 1. file cua goi
    need = ["config.json", cfg["snapshot_path"], "src/common.py", "src/data_prep.py", "src/integrate.py",
            "src/bisection.py", "src/validate.py", "src/experiments.py", "src/run_all.py"]
    for rel in need:
        ok = (ROOT / rel).exists()
        add("co_file:" + rel, "co" if ok else "THIEU", "OK" if ok else "ERROR")
    snap = ROOT / cfg["snapshot_path"]
    if not snap.exists():
        finish("Khong thay %s. Chep shared/analysis_snapshot.csv vao thu muc data/ (khong tu tao du lieu)." % snap)
    df = pd.read_csv(snap, encoding="utf-8-sig")

    # 2. schema
    miss = [c for c in SCHEMA if c not in df.columns]
    add("schema_du_cot", "thieu: " + ",".join(miss) if miss else "du %d cot" % len(SCHEMA), "ERROR" if miss else "OK")
    if miss:
        finish("Snapshot thieu cot theo schema 2.2.")
    bad_id = df[~df["image_id"].astype(str).str.match(HEX64)]
    add("image_id_la_SHA256_64_hex", len(bad_id), "OK" if bad_id.empty else "ERROR")

    # 3. timestamp
    bad_ts = df[~df["timestamp"].astype(str).str.match(ISO)]
    add("timestamp_ISO8601_+07:00_co_giay", len(bad_ts), "OK" if bad_ts.empty else "ERROR")
    bad_src = df[~df["time_source"].isin(TIME_SOURCES)]
    add("time_source_hop_le", len(bad_src), "OK" if bad_src.empty else "WARN")

    # 4. nhan
    bad_lab = df[~df["label_status"].isin(LABEL_OK)]
    add("label_status_hop_le", len(bad_lab), "OK" if bad_lab.empty else "ERROR")

    # 5. tong
    cls = df[["count_2wheel", "count_bus", "count_car", "count_truck"]].sum(axis=1)
    bad_sum = df[cls != df["total_count"]]
    add("total_count_bang_tong_4_lop", len(bad_sum), "OK" if bad_sum.empty else "ERROR")

    # 6. trung -> danh sach loai
    dup_id = df[df.duplicated("image_id", keep="first")]
    dup_ct = df[df.duplicated(["camera_id", "timestamp"], keep="first")]
    removed = pd.concat([dup_id.assign(ly_do="trung image_id"), dup_ct.assign(ly_do="trung camera_id + timestamp")])
    removed = removed.drop_duplicates(subset=["image_id", "ly_do"])
    removed[["image_id", "camera_id", "recording_id", "timestamp", "analysis_segment", "ly_do"]].to_csv(
        results_dir() / "removed_records.csv", index=False, encoding="utf-8-sig")
    add("trung_image_id", len(dup_id), "OK" if dup_id.empty else "ERROR")
    add("trung_camera_timestamp", len(dup_ct), "OK" if dup_ct.empty else "ERROR")
    add("danh_sach_loai_removed_records.csv", "%d dong" % len(removed), "INFO")

    # 7. recording vs ngay timestamp
    day = df["timestamp"].astype(str).str.slice(0, 10)
    rec_day = df["recording_id"].astype(str).str.extract(r"(\d{4}-\d{2}-\d{2})")[0]
    mism = df[(day != rec_day) & rec_day.notna()]
    add("recording_id_khop_ngay_timestamp", len(mism), "OK" if mism.empty else "ERROR")
    add("recording_id_co_ngay", int(rec_day.isna().sum()), "OK" if rec_day.notna().all() else "WARN")

    # 8. hai doan
    ranges = {}
    for seg in cfg["segments"]:
        s = df[df["analysis_segment"] == seg]
        if s.empty:
            add("doan_%s_ton_tai" % seg, "KHONG CO -> ghi thieu, khong tu tao", "ERROR")
            continue
        n = len(s)
        add("doan_%s_so_quan_sat" % seg, n, "OK" if cfg["min_obs"] <= n <= cfg["max_obs"] else "ERROR")
        add("doan_%s_1_camera_1_recording" % seg, "%d camera, %d recording" % (
            s["camera_id"].nunique(), s["recording_id"].nunique()),
            "OK" if s["camera_id"].nunique() == 1 and s["recording_id"].nunique() == 1 else "ERROR")
        add("doan_%s_1_trang_thai_nhan" % seg, ",".join(sorted(s["label_status"].unique())) + " / " + ",".join(
            sorted(s["label_version"].astype(str).unique())),
            "OK" if s["label_status"].nunique() == 1 and s["label_version"].nunique() == 1 else "ERROR")
        ts = pd.to_datetime(s["timestamp"], utc=True).dt.tz_convert("Asia/Ho_Chi_Minh")
        ranges[seg] = (ts.min(), ts.max(), s["recording_id"].iloc[0])
    if len(ranges) == 2:
        (a0, a1, ra), (b0, b1, rb) = ranges[cfg["segments"][0]], ranges[cfg["segments"][1]]
        add("hai_doan_khac_recording", "%s | %s" % (ra, rb), "OK" if ra != rb else "ERROR")
        add("hai_doan_khong_giao_nhau", "A %s..%s ; B %s..%s" % (a0.strftime("%m-%d %H:%M"), a1.strftime("%H:%M"),
                                                                b0.strftime("%m-%d %H:%M"), b1.strftime("%H:%M")),
            "OK" if (a1 < b0 or b1 < a0) else "ERROR")
        both = set(df[df["analysis_segment"] == cfg["segments"][0]]["label_status"]) | set(
            df[df["analysis_segment"] == cfg["segments"][1]]["label_status"])
        add("hai_doan_cung_trang_thai_nhan", ",".join(sorted(both)), "OK" if len(both) == 1 else "ERROR")

    # 9. theo goi (tuy chon)
    if a.root:
        root = Path(a.root)
        for rel in ["README.md", "shared/classes.yaml", "shared/roi_definitions.json",
                    "shared/camera_mapping.csv", "shared/analysis_snapshot.csv"]:
            ok = (root / rel).exists()
            add("goi_co_file:" + rel, "co" if ok else "THIEU (ghi nhan su co ban giao)", "OK" if ok else "ERROR")
        missing = [p for p in df["image_path"] if not (root / p).exists()]
        add("anh_trong_image_path_ton_tai", "%d/%d thieu" % (len(missing), len(df)),
            "OK" if not missing else "WARN")
    else:
        add("kiem_tra_theo_goi (--root)", "bo qua: khong truyen --root", "INFO")

    finish()


def finish(msg=""):
    with open(results_dir() / "input_check.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["check", "value", "level"])
        w.writerows(REPORT)
    print("%-44s %-46s %s" % ("Kiem tra", "Gia tri", "Muc"))
    for r in REPORT:
        print("%-44s %-46s %s" % (r[0], str(r[1])[:46], r[2]))
    err = [r for r in REPORT if r[2] == "ERROR"]
    if msg:
        print("\n" + msg)
    if err or msg:
        print("\nCO %d LOI (ERROR): xem results/input_check.csv. Khong chay buoc sau." % max(len(err), 1))
        sys.exit(1)
    print("\nDAU VAO HOP LE (nhan van la prelabel -> ket qua SO BO).\n")


if __name__ == "__main__":
    main()
