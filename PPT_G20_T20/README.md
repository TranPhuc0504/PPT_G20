# Nhóm 20 — Đề tài 20 — Thời điểm đạt chỉ số tải tích lũy

Cho số xe y(t) theo thời gian trên một đoạn camera, tìm thời điểm T sao cho tải tích lũy

    I(T) = ∫ y(t) dt  (từ đầu đoạn đến T)

đạt mức Q = q · I_tot, với q = 25%, 50%, 75%. Tích phân bằng **quy tắc hình thang** (nối thẳng giữa các ảnh),
tìm T bằng **phương pháp chia đôi**. Cả hai đều tự lập trình bằng float64, không dùng hàm giải sẵn của thư viện.

> **Kết quả là SƠ BỘ.** Dữ liệu camera hiện mang nhãn `unreviewed_prelabel` (chưa nghiệm thu). Không tự đổi
> trạng thái nhãn. Khi có snapshot chính thức (Tuần 5) chỉ cần chạy lại (mục 9.4).

---

## 1. Nộp theo tuần

### Tuần 2 — Kiểm chứng trên hàm biết trước nghiệm đúng

| Yêu cầu | Nằm ở đâu |
|---|---|
| Tự lập trình thuật toán bằng float64, không dùng hàm giải sẵn | `src/mo_hinh.py` (Phần 2 tích phân, Phần 3 chia đôi) |
| Chạy kiểm chứng trên hàm biết trước nghiệm đúng (y = 1 + t) | `src/kiem_chung.py` |
| Bảng sai số MAE, RMSE, E∞ | `results/verify_linear.csv` (dòng `tong_hop` của mỗi dung sai) |
| Kiểm chứng khi làm thưa lưới f1, f2, f4 | `results/verify_thin.csv` (dòng `tong_hop` của mỗi lưới, dòng cuối là p) |
| Bậc hội tụ thực nghiệm p = log2(E_h / E_{h/2}) trên `analysis_snapshot.csv` | `results/sampling_summary.csv`, dòng `chi_bao_p` |

Kết quả: mục 7.

### Tuần 3 — Thí nghiệm trên snapshot (đoạn A/B) và khảo sát độ nhạy

| Yêu cầu | Nằm ở đâu |
|---|---|
| Dùng trực tiếp `shared/analysis_snapshot.csv` | `src/chuan_bi_du_lieu.py` đọc bản chép nguyên vẹn `data/analysis_snapshot.csv` |
| Chạy ứng dụng trên 2 đoạn A/B | `src/mo_hinh.py` → `results/integral_summary.csv`, `results/bisection_results.csv` |
| Bảng Q, T, residual, số vòng, độ rộng khoảng cuối; phân biệt phút / xe·phút | `results/bisection_results.csv` |
| Khảo sát độ nhạy: bước lưới h0, 2h0, 4h0 (lưới f1, f2, f4) | `results/sampling_summary.csv` |
| (Đề 20) Biến động do dung sai thuật toán | `results/tolerance_study.csv` |

Tham số điều chuẩn: không áp dụng (Đề 20 không có). Thêm nhiễu: đề tài không yêu cầu. Kết quả: mục 8.

### Tuần 4 — Phương án chia tập, pipeline và đồ thị

| Yêu cầu | Nằm ở đâu |
|---|---|
| Chốt phương án chia tập | Mục 9.1: **nút dựng / điểm kiểm tra** |
| Hoàn tất toàn bộ pipeline code | `chuan_bi_du_lieu.py` → `mo_hinh.py` → `kiem_chung.py` → `ve_do_thi.py` (mục 3) |
| Kịch bản vẽ đồ thị | `src/ve_do_thi.py` → thư mục `figures/` (mục 9.3) |
| Sẵn sàng chạy lại khi có snapshot chính thức | Mục 9.4 |

---

## 2. Cấu trúc thư mục

```
config.json                  tham số: đoạn, mức Q, dung sai, hệ số làm thưa, kiểm chứng
README.md
data/
  analysis_snapshot.csv      bản chép nguyên vẹn của shared/analysis_snapshot.csv
  segment_A.csv, segment_B.csv           danh sách ảnh của từng đoạn         (tạo ra)
  grid_{A,B}_timestamps_f{1,2,4}.csv     lưới t_min, y                        (tạo ra)
src/
  chuan_bi_du_lieu.py        đọc snapshot, kiểm tra, tạo lưới f1, f2, f4
  mo_hinh.py                 tích phân, chia đôi, khảo sát, ghi kết quả, menu tính riêng
  kiem_chung.py              kiểm chứng y = 1 + t (theo dung sai và theo làm thưa)
  ve_do_thi.py               vẽ 3 hình
results/                     các bảng kết quả .csv                               (tạo ra)
figures/                     các hình .png                                       (tạo ra)
```

| File code | Nội dung |
|---|---|
| `chuan_bi_du_lieu.py` | Lọc ảnh theo cột `analysis_segment` (A/B), sắp theo thời gian, kiểm tra dữ liệu, đổi thời gian ra phút tính từ ảnh đầu, lấy y = `total_count`, làm thưa giữ hai đầu |
| `mo_hinh.py` | Phần 1 cấu hình; Phần 2 tích phân hình thang (`cumulative`, `locate`, `I_of_T`); Phần 3 chia đôi (`bisect`); Phần 4 khảo sát làm thưa và dung sai; Phần 5 lập bảng, ghi CSV, in kết quả, menu |
| `kiem_chung.py` | So T chia đôi với nghiệm đúng T\* trên y = 1 + t; dùng lại đúng các hàm của `mo_hinh.py` và quy tắc làm thưa của `chuan_bi_du_lieu.py` |
| `ve_do_thi.py` | Vẽ hình từ lưới trong `data/` và bảng trong `results/`; không tính bài toán mới |

---

## 3. Cài đặt và chạy

```
pip install numpy matplotlib
```

Chạy từ thư mục gốc (nơi có `config.json`), theo thứ tự:

```
python src\chuan_bi_du_lieu.py       # 1. tạo lưới từ snapshot (dừng nếu có ERROR)
python src\mo_hinh.py --het          # 2. chạy mô hình trên A/B, ghi 4 bảng vào results/
python src\kiem_chung.py             # 3. kiểm chứng y = 1 + t, ghi 2 bảng vào results/
python src\ve_do_thi.py              # 4. vẽ 3 hình vào figures/
```

- `python src\mo_hinh.py` (không kèm tùy chọn) mở menu: **1** chạy hết, **2** tính riêng (nhập k, T hoặc q), **3** kiểm chứng.
- `python src\mo_hinh.py --demo` mở thẳng menu tính riêng.
- Nếu báo `PermissionError`: đóng file .csv đang mở trong Excel rồi chạy lại.

---

## 4. Các file kết quả (`results/`)

| File | Tạo bởi | Nội dung | Đơn vị |
|---|---|---|---|
| `data_validation.csv` | `chuan_bi_du_lieu.py` | Kiểm tra dữ liệu từng đoạn: số ảnh, trùng thời điểm, khoảng trống, recording, số xe, số mốc lưới | |
| `integral_summary.csv` | `mo_hinh.py` | Mỗi đoạn × lưới: số mốc, thời gian phủ, I_tot, số xe trung bình, 3 mức Q (chốt từ f1) | phút; xe·phút |
| `bisection_results.csv` | `mo_hinh.py` | Mỗi đoạn × lưới × q: Q, T, số vòng, độ rộng khoảng cuối, residual \|I(T) − Q\|, I(T) | T, độ rộng: phút; Q, residual, I: xe·phút |
| `sampling_summary.csv` | `mo_hinh.py` | Độ lệch T của f2, f4 so với f1: MAE, RMSE, E∞; chỉ báo p | phút |
| `tolerance_study.csv` | `mo_hinh.py` | Lưới f1, từng q × dung sai: số vòng, T, \|T(tol) − T(10⁻⁶)\|, residual | phút; residual: xe·phút |
| `verify_linear.csv` | `kiem_chung.py` | y = 1 + t, từng dung sai × Q: T\*, T, \|T − T\*\|, residual, số vòng; dòng `tong_hop`: MAE, RMSE, E∞ | phút; residual: xe·phút |
| `verify_thin.csv` | `kiem_chung.py` | y = 1 + t, lưới f1, f2, f4 × Q: T\*, T, \|T − T\*\|; dòng `tong_hop`: MAE, RMSE, E∞; dòng cuối: p | phút |

---

## 5. Dữ liệu

Nguồn: `shared/analysis_snapshot.csv` của giảng viên, chép nguyên vẹn vào `data/`. Đoạn A/B lấy theo cột
`analysis_segment` có sẵn; số xe lấy thẳng từ cột `total_count`. Không tự đếm lại từ ảnh, không tự tạo dữ liệu.

| Đoạn | Recording | Số ảnh | Đầu (+07:00) | Cuối (+07:00) | Độ dài (phút) | Bước trung vị h0 |
|---|---|---:|---|---|---:|---:|
| A | camnutgiaocaygo3_2026-07-13_R01 | 100 | 2026-07-13 06:08:41 | 2026-07-13 07:17:09 | 68.4667 | 37 s |
| B | camnutgiaocaygo3_2026-07-16_R01 | 100 | 2026-07-16 00:00:22 | 2026-07-16 00:48:55 | 48.5500 | 25 s |

**Kiểm tra** (`results/data_validation.csv`): số ảnh 80–300; không trùng thời điểm; không khoảng trống quá 3 lần
bước trung vị; cùng một recording; số xe không âm. Cả hai đoạn đạt; `label_status` báo WARN vì là prelabel.

**Lưới:** dùng **thời điểm chụp thật** (không đều).
- f1: toàn bộ 100 ảnh, bước ≈ h0.
- f2: giữ mốc 0, 2, 4, … → 51 mốc, bước ≈ 2h0.
- f4: giữ mốc 0, 4, 8, … → 26 mốc, bước ≈ 4h0.

Lưới thưa luôn giữ mốc cuối (cùng hai đầu với f1); y giữ nguyên, không tính lại.

---

## 6. Mô hình và thuật toán

- **Tích phân hình thang:** I_0 = 0, I_{k+1} = I_k + h_k (y_k + y_{k+1}) / 2.
- **Tải tại T bất kỳ:** tìm khoảng k chứa T (tìm nhị phân), s = T − t_k, m_k là độ dốc trong khoảng:
  I(T) = I_k + y_k s + m_k s² / 2.
- **Chia đôi:** giải F(T) = I(T) − Q = 0 trên [t_0, t_N]. Nếu F(m) ≥ 0 thì b = m, ngược lại a = m. Dừng khi
  b − a ≤ tol = 10⁻⁶ phút hoặc hết 100 vòng. Lấy **T = (a + b) / 2** (đang chờ giảng viên xác nhận (a+b)/2 hay b).
- **Q chốt từ lưới gốc f1** và dùng lại cho f2, f4.
- **Đơn vị:** T, độ rộng khoảng, sai số và độ lệch của T tính bằng **phút**; Q, I, residual \|I(T) − Q\| tính bằng **xe·phút**.

---

## 7. Kết quả Tuần 2 — Kiểm chứng

Hàm y = 1 + t trên [0, 1], 10 khoảng. I(T) = T + T²/2, nghiệm đúng T\* = −1 + √(1 + 2Q), tính dạng ổn định
2Q / (1 + √(1 + 2Q)) để tránh trừ hai số gần nhau. Q = 0.375; 0.75; 1.125 (0 < Q < 1.5).

**Tiêu chí đạt:** \|T − T\*\| ≤ tol/2 với mọi Q (cận lý thuyết của chia đôi khi lấy trung điểm). Kết quả: **ĐẠT**.

### 7.1 Theo dung sai (`verify_linear.csv`)

| tol (phút) | Số vòng | MAE | RMSE | E∞ |
|---|---:|---:|---:|---:|
| 10⁻³ | 10 | 3.243e-04 | 3.550e-04 | 4.470e-04 |
| 10⁻⁶ | 20 | 2.118e-07 | 2.160e-07 | 2.576e-07 |
| 10⁻⁹ | 30 | 9.712e-11 | 1.198e-10 | 1.896e-10 |

- I_tot tính ra đúng 1.5: hình thang chính xác với hàm bậc nhất.
- Dung sai nhỏ đi 1000 lần thì thêm 10 vòng (2¹⁰ ≈ 1000) và sai số giảm cùng tỉ lệ.

### 7.2 Theo làm thưa lưới (`verify_thin.csv`, tol = 10⁻⁶)

| Lưới | Số mốc | MAE | RMSE | E∞ |
|---|---:|---:|---:|---:|
| f1 | 11 | 2.118e-07 | 2.160e-07 | 2.576e-07 |
| f2 | 6 | 2.118e-07 | 2.160e-07 | 2.576e-07 |
| f4 | 4 | 2.118e-07 | 2.160e-07 | 2.576e-07 |

p = log2(E_f4 / E_f2) = **0**. Hình thang chính xác với hàm bậc nhất nên sai số không phụ thuộc bước lưới, chỉ còn
do dung sai chia đôi. Vì vậy bậc hội tụ p được đo trên dữ liệu snapshot (mục 8.2).

---

## 8. Kết quả Tuần 3 — Thí nghiệm trên snapshot

### 8.1 Thời điểm T trên lưới gốc f1 (tol = 10⁻⁶ phút)

| Đoạn | I_tot (xe·phút) | q | Q (xe·phút) | T (phút từ đầu đoạn) | Vòng | Residual (xe·phút) |
|---|---:|---|---:|---:|---:|---:|
| A | 1438.925 | 25% | 359.731 | 17.806182 | 27 | 6.7e-06 |
| A | | 50% | 719.463 | 37.443147 | 27 | 4.9e-06 |
| A | | 75% | 1079.194 | 53.288040 | 27 | 4.7e-07 |
| B | 246.392 | 25% | 61.598 | 11.630729 | 26 | 6.9e-08 |
| B | | 50% | 123.196 | 25.026042 | 26 | 1.3e-06 |
| B | | 75% | 184.794 | 35.936018 | 26 | 1.1e-06 |

Đầy đủ cho f1, f2, f4 (kèm độ rộng khoảng cuối): `results/bisection_results.csv`.

### 8.2 Khảo sát làm thưa lưới (độ lệch T so với lưới gốc f1, phút)

| Đoạn | Lưới | MAE | RMSE | E∞ |
|---|---|---:|---:|---:|
| A | f2 (≈2h0) | 0.5565 | 0.5836 | 0.7687 |
| A | f4 (≈4h0) | 2.7505 | 2.9363 | 4.2017 |
| B | f2 (≈2h0) | 1.7696 | 2.1131 | 3.1332 |
| B | f4 (≈4h0) | 1.2360 | 1.2454 | 1.4522 |

Chỉ báo bậc p = log2(E_f4 / E_f2): A = 2.451, B = −1.109. Số xe dao động mạnh (dữ liệu có nhiễu) nên p chỉ để
tham khảo, không dùng để kết luận bậc hội tụ. Dữ liệu thật không có nghiệm đúng, nên các số trên là **độ lệch so với
lưới gốc**, không phải sai số so với thực tế.

### 8.3 Khảo sát dung sai (lưới f1, so với T ở tol chính thức 10⁻⁶)

| tol | Vòng (A / B) | Độ lệch lớn nhất \|T(tol) − T(10⁻⁶)\| (A / B, phút) |
|---|---|---|
| 10⁻³ | 17 / 16 | 2.6e-04 / 3.2e-04 |
| 10⁻⁶ | 27 / 26 | 0 / 0 (mốc so sánh) |
| 10⁻⁹ | 36 / 36 | 2.1e-07 / 3.4e-07 |

### 8.4 So sánh hai nguồn biến động (Bước 5)

- Do **lấy mẫu** (làm thưa lưới): E∞ lớn nhất **4.2 phút**.
- Do **dung sai** chia đôi 10⁻⁶: khoảng **3 × 10⁻⁷ phút**.

Trên cả hai đoạn, biến động do lấy mẫu lớn hơn khoảng một triệu lần. Độ tin cậy của T bị giới hạn bởi mật độ ảnh,
không phải bởi thuật toán; tol = 10⁻⁶ là đủ.

---

## 9. Tuần 4 — Phương án chia tập, pipeline và đồ thị

### 9.1 Phương án chia tập: nút dựng / điểm kiểm tra

Đề 20 là bài nội suy và tích phân, **không có tham số để học hay khớp**, nên không dùng train/val/test.

| | Đề 20 |
|---|---|
| **Nút dựng** | Mốc của lưới đang tính: f1 (100 ảnh), f2 (51 mốc), f4 (26 mốc); luôn giữ mốc đầu và mốc cuối |
| **Điểm kiểm tra** | Trên dữ liệu A/B: T tính trên lưới gốc f1 làm mốc so sánh cho f2, f4. Trên bài kiểm chứng: nghiệm đúng T\* |

### 9.2 Pipeline

```
data/analysis_snapshot.csv
   → chuan_bi_du_lieu.py   (kiểm tra, tạo lưới f1, f2, f4)     → data/, results/data_validation.csv
   → mo_hinh.py            (tích phân, chia đôi, khảo sát)     → 4 bảng trong results/
   → kiem_chung.py         (kiểm chứng y = 1 + t)               → 2 bảng trong results/
   → ve_do_thi.py          (vẽ hình)                           → 3 hình trong figures/
```

Mọi tham số đọc từ `config.json`; mọi đường dẫn tính từ thư mục gốc. Không có số nào viết cứng trong code.

### 9.3 Đồ thị (`figures/`)

| Hình | Nội dung | Gắn với đề |
|---|---|---|
| `hinh1_tai_tich_luy.png` | Số xe ỹ(t) và tải tích lũy I(t) của A/B; giao mức Q (xe·phút) tại T (phút) | Sản phẩm bắt buộc: đồ thị tích lũy và giao mức |
| `hinh2_kiem_chung.png` | Kiểm chứng: E∞ theo dung sai (thang log), kèm cận tol/2 | Bước 4 |
| `hinh3_so_sanh.png` | Biến động lớn nhất của T: làm thưa f2, f4 so với dung sai 10⁻⁶ (thang log) | Bước 5 |

### 9.4 Chạy lại khi có snapshot chính thức (Tuần 5)

1. Đổi tên `data/` → `data_prelabel/`, `results/` → `results_prelabel/`, `figures/` → `figures_prelabel/` (giữ để so sánh).
2. Tạo `data/` mới, chép `analysis_snapshot.csv` chính thức vào (giữ đúng tên file).
3. Chạy lại 4 lệnh ở mục 3. Không cần sửa code.
4. Nếu `chuan_bi_du_lieu.py` báo ERROR: dừng và báo giảng viên, không tự sửa dữ liệu.
5. Cập nhật số liệu trong báo cáo; bỏ chữ "sơ bộ" khi nhãn đã là `human_verified`.

---

## 10. Giới hạn và quy định

- Kết quả hiện tại là **sơ bộ** (nhãn prelabel).
- Cách lấy T = (a + b)/2 đang chờ giảng viên xác nhận.
- Không chia sẻ công khai ảnh, nhãn hay review log. Repo để chế độ private; chỉ các bảng số trong `data/` và
  `results/` đi kèm bài nộp.
