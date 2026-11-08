# Nhóm 20 — Đề tài 20 — Thời điểm đạt chỉ số tải tích lũy

Đề tài: cho hàm tải y(t) (số xe hiện diện theo thời gian), tìm thời điểm T sao cho tích phân tích lũy
I(T) = ∫ y(t) dt từ đầu đoạn đến T đạt ngưỡng Q (25%, 50%, 75% tổng tải của đoạn).

## 1. Phạm vi và trạng thái

Gói này gồm hai giai đoạn:

- **Tuần 1:** chọn, kiểm tra hai đoạn A/B và chuẩn bị dữ liệu (`check_input.py`, `data_prep.py`).
- **Tuần 2:** phần tính toán chính — tích phân hình thang, chia đôi, kiểm chứng trên hàm biết nghiệm đúng, bảng sai số
  MAE/RMSE/E_inf, bậc hội tụ p, khảo sát làm thưa lưới và dung sai (`integrate.py`, `bisection.py`, `validate.py`,
  `experiments.py`).

### Nộp Tuần 2 (script kiểm chứng và bảng sai số)

| Yêu cầu | Nằm ở đâu |
|---|---|
| Script kiểm chứng (tự cài đặt, float64); kiểm chứng hàm có nghiệm đúng | `src/validate.py` (kèm `src/integrate.py`, `src/bisection.py`, `src/common.py`, `config.json`) |
| Bảng sai số MAE, RMSE, E_inf | `results/verify_linear_summary.csv` (chi tiết: `results/verify_linear.csv`) |
| Bậc hội tụ thực nghiệm p = log2(E_h / E_{h/2}) trên dữ liệu `analysis_snapshot.csv` | `results/sampling_summary.csv` (cột `chi_bao_p`; chi tiết: `results/sampling_effect.csv`) |

Dữ liệu camera hiện mang nhãn `unreviewed_prelabel` (PRELABEL, chưa nghiệm thu). Mọi con số tính từ dữ liệu
này là **SƠ BỘ**, không phải ground truth. Không tự đổi trạng thái nhãn thành `human_verified`.

## 2. Thành phần gói

| Đường dẫn | Nội dung |
|---|---|
| `config.json` | Tham số của dự án: seed 2026, kiểu `float64`, các kiểu lưới gốc, hệ số làm thưa lưới, các mức Q, dung sai chia đôi, đơn vị |
| `data/analysis_snapshot.csv` | Bản chép của `shared/analysis_snapshot.csv` (giảng viên cung cấp). Tự chép vào trước khi chạy |
| `data/segment_A.csv`, `data/segment_B.csv` | Hai đoạn quan sát nguồn (giữ nguyên số đếm và nhãn); cột `t_min` là thời gian tính bằng phút từ mốc đầu đoạn |
| `data/grid_A_timestamps_f1.csv`, `grid_B_timestamps_f1.csv` | **Lưới gốc chính:** timestamp thật (100 mốc, không đều). Cơ sở: Quy định 2.3 mục 4 (nội suy/hình thang cho phép timestamp không đều) |
| `data/grid_*_timestamps_f2.csv`, `..._f4.csv` | **Làm thưa mỗi 2 / mỗi 4 mốc** của lưới gốc chính (giữ mốc 0, 2, 4… / 0, 4, 8…), `y` giữ nguyên, luôn giữ mốc cuối nên cùng hai đầu |
| `src/common.py` | Hàm dùng chung: đọc cấu hình, đặt seed, đường dẫn tương đối, kiểu `float64` |
| `src/check_input.py` | **Bước 00:** kiểm tra đầu vào theo Quy định 2.1, 2.3 (mục 4.4); ghi `input_check.csv`, `removed_records.csv` |
| `src/data_prep.py` | Đọc snapshot, kiểm tra hai đoạn A/B, đổi thời gian ra phút, tạo các lưới |
| `src/integrate.py` | Tích phân hình thang tự cài: mảng tích lũy `I`, tìm khoảng `locate`, `I(T)`, `F(T) = I(T) − Q`, các mức Q |
| `src/bisection.py` | Chia đôi tự cài tìm T cho Q = 25%, 50%, 75% trên mọi đoạn, lưới, mức làm thưa |
| `src/validate.py` | Bước 4: kiểm chứng trên hàm biết nghiệm đúng y = 1 + t; sai số nghiệm, residual, MAE/RMSE/E_inf |
| `src/experiments.py` | Bước 5: ảnh hưởng của làm thưa lưới (f2, f4), bậc hội tụ thực nghiệm p và dung sai chia đôi |
| `src/demo.py` | Chạy thử tương tác: nhập T, k hoặc q; chọn đoạn và mức làm thưa; hiển thị sai số dạng 10^-6 |
| `src/run_all.py` | Chạy lần lượt các bước 00 → 5; bước chưa có file (như `make_figures`) tự được bỏ qua |
| `results/data_validation.csv` | Bảng kiểm tra dữ liệu A/B (giải thích ở mục 4) |
| `results/input_check.csv`, `removed_records.csv` | Kết quả kiểm tra đầu vào; danh sách bản ghi bị loại (rỗng nếu không có) |
| `results/integral_summary.csv`, `bisection_results.csv` | Tổng tải I_tot, Q; nghiệm T, số vòng, độ rộng khoảng, residual |
| `results/verify_linear.csv`, `verify_linear_summary.csv` | Bảng kiểm chứng và sai số MAE/RMSE/E_inf (mục 7.3) |
| `results/sampling_*.csv`, `tolerance_study.csv` | Khảo sát làm thưa lưới và dung sai (mục 7.4) |
| `README.md` | Hướng dẫn và giới hạn sử dụng |

## 3. Nguồn dữ liệu

Nguồn: `shared/analysis_snapshot.csv` trong gói Traffic_BTL do giảng viên cung cấp; không tự đếm lại từ ảnh
để thay snapshot, không tự tạo timestamp hay dữ liệu mô phỏng.

| Đoạn | Recording | Số quan sát | Thời điểm đầu (+07:00) | Thời điểm cuối (+07:00) | Độ dài (phút) |
|---|---|---:|---|---|---:|
| A | camnutgiaocaygo3_2026-07-13_R01 | 100 | 2026-07-13 06:08:41 | 2026-07-13 07:17:09 | 68,4667 |
| B | camnutgiaocaygo3_2026-07-16_R01 | 100 | 2026-07-16 00:00:22 | 2026-07-16 00:48:55 | 48,5500 |

Hai đoạn được xử lý riêng, không ngoại suy và không nội suy qua khoảng trống (gap) lớn.

## 4. Tại sao chọn hai đoạn dữ liệu này, và vì sao hợp lệ

### 4.1. Lý do chọn

- **Quy định yêu cầu chọn trong snapshot chung** (Quy định 2.3, điểm 2): "Chọn đoạn đủ điều kiện trong snapshot chung".
  Snapshot giảng viên phát có đúng 200 quan sát, chia thành hai đoạn A (100 quan sát) và B (100 quan sát).
  Nhóm dùng nguyên hai đoạn này, không lọc, không bỏ bớt ảnh và không chọn theo kết quả tính.
- **Hai đoạn thoả điều kiện của đề** (Quy định 2.3, điểm 1): hai đoạn độc lập, cùng camera (`camnutgiaocaygo3`),
  khác ngày (13/7 và 16/7), khác recording, không giao nhau về thời gian; mỗi đoạn 80–300 quan sát và cùng trạng thái nhãn.
- **Hai đoạn có đặc tính tải khác nhau**, giúp thử thuật toán trên hai chế độ: A là buổi sáng (06:08–07:17), tải cao
  và dao động mạnh (số xe 5–75, trung bình khoảng 21); B là gần nửa đêm (00:00–00:48), tải thấp (0–12, trung bình
  khoảng 5). Số liệu này tính từ nhãn PRELABEL nên chỉ là sơ bộ.
- **Không có gap lớn nên không phải tách đoạn** (Quy định 2.3, điểm 3): bước thời gian giữa hai ảnh liên tiếp đều
  dưới ngưỡng 3 lần trung vị (xem bảng dưới).

### 4.2. Cách kiểm tra và đọc kết quả `results/data_validation.csv`

Chạy `python src/run_all.py` (hoặc `python src/data_prep.py`) sẽ ghi bảng này. Cột: `segment` (đoạn A/B),
`check` (tên phép kiểm), `value` (kết quả đo), `level` (mức đánh giá):

- `OK`: đạt điều kiện; `INFO`: thông tin tham khảo; `WARN`: cảnh báo, không dừng; `ERROR`: vi phạm quy định, chương trình dừng.

**Nhóm 1 — Điều kiện của đoạn** (đều đạt):

| `check` | A / B | Ý nghĩa |
|---|---|---|
| `so_quan_sat` | 100 / 100 | Số ảnh trong đoạn; quy định cần 80–300 |
| `trung_timestamp` | 0 / 0 | Số cặp ảnh cùng thời điểm; phải bằng 0 để thời gian tăng nghiêm ngặt |
| `gap_lon_hon_3x_trung_vi` | 0 / 0 | Số khoảng trống dài hơn 3 lần trung vị bước dương; bằng 0 nghĩa là không có chỗ mất dữ liệu lớn |
| `so_recording` | 1 / 1 | Số phiên ghi hình trong đoạn; phải là 1 để không ghép hai phiên rời |
| `y_am_hoac_khong_huu_han` | 0 / 0 | Số giá trị `y` âm hoặc lỗi (NaN, vô cực); phải bằng 0 |

**Nhóm 2 — Thông tin về bước thời gian** (INFO):

| `check` | A / B | Ý nghĩa |
|---|---|---|
| `buoc_min_s` | 36 / 24 giây | Khoảng cách ngắn nhất giữa hai ảnh liên tiếp |
| `buoc_trung_vi_s` | 37 / 25 giây | Khoảng cách điển hình; ngưỡng gap = 3 × trung vị = 111 giây (A), 75 giây (B) |
| `buoc_max_s` | 74 / 50 giây | Khoảng cách dài nhất; vẫn dưới ngưỡng gap nên không có gap |
| `do_dai_doan_phut` | 68,4667 / 48,55 | Độ dài cả đoạn từ ảnh đầu đến ảnh cuối, tính bằng phút |

**Nhóm 3 — Cảnh báo nhãn** (WARN): `label_status = unreviewed_prelabel` ở cả hai đoạn. Nhãn chưa được nghiệm thu
nên mọi kết quả phải ghi là sơ bộ. Đây là cảnh báo có chủ ý, không phải lỗi.

**Nhóm 4 — Lưới** (tên dạng `luoi_<kiểu>_<f>_...`):

| `check` | Ý nghĩa |
|---|---|
| `luoi_timestamps_f1_so_moc` | Số mốc lưới timestamp thật: 100 ở cả hai đoạn |
| `luoi_timestamps_f2/f4_...` | 51 mốc và 26 mốc, vẫn giữ mốc đầu và mốc cuối thật (A: 0–68,4667; B: 0–48,55) |

**Kết luận:** cột `level` của hai đoạn chỉ có OK, INFO và một dòng WARN về nhãn, không có ERROR, nên dữ liệu
đủ điều kiện để chạy bước tiếp theo.

### 4.3. "Hợp lệ" ở đây có nghĩa gì

- **Có nghĩa:** hai đoạn thoả các điều kiện trong Quy định mục 2.3 mà nhóm kiểm tra bằng code (`data_prep.py`).
- **Không có nghĩa:** dữ liệu đã được giảng viên nghiệm thu. Bảng này do nhóm tự kiểm tra, không phải công cụ QC
  của giảng viên (`qc_dataset.py` dùng cho nhãn ảnh ở Phần 1).
- **Giới hạn hiện tại:** khi gặp khoảng trống lớn hơn 3 lần trung vị, quy định yêu cầu *tách đoạn*; code hiện *dừng và
  báo ERROR* để nhóm xử lý. Với dữ liệu hiện tại không có gap nên không xảy ra. Việc đối chiếu
  tên recording với ngày của timestamp và ghi danh sách bản ghi bị loại do `check_input.py` đảm nhiệm (mục 4.4).

### 4.4. Kiểm tra đầu vào trước khi chạy (`src/check_input.py`, bước 00)

Chạy riêng `python src/check_input.py` (hoặc tự động qua `run_all.py`). Thêm `--root <thư mục gói Traffic_BTL>` để kiểm tra
thêm các file README/classes/roi và ảnh trong `image_path` có thật. Chương trình kiểm tra theo Quy định 2.1, 2.3:

1. Đủ file của gói Phần 2 (`config.json`, snapshot, các script trong `src/`).
2. Snapshot đủ cột theo schema; `image_id` là SHA256 (64 ký tự hex).
3. `timestamp` theo ISO 8601 có `+07:00` và có giây; `time_source` hợp lệ.
4. `label_status` chỉ thuộc `human_verified` hoặc `unreviewed_prelabel`, không trộn trong một đoạn; `label_version` thống nhất.
5. `total_count` bằng tổng bốn lớp (2 bánh, bus, car, truck).
6. Trùng `image_id`, trùng camera/timestamp: ghi vào `results/removed_records.csv` (danh sách loại; rỗng nếu không có).
7. Tên `recording_id` (có ngày) khớp ngày của timestamp.
8. Hai đoạn A/B: mỗi đoạn một camera, một recording, 80–300 quan sát; khác recording và không giao nhau về thời gian.

Kết quả ghi vào `results/input_check.csv` (cột `check`, `value`, `level` như bảng ở mục 4.2). Mức `ERROR` làm chương trình thoát với mã lỗi 1.
Chương trình không tự tạo ảnh, nhãn hay timestamp để lấp chỗ thiếu (Quy định 2.1).

## 5. Lưới gốc và làm thưa lưới

- `segment_A.csv`, `segment_B.csv` là đầu vào chính: timestamp thật (ISO 8601), giữ nguyên giây.
- **Lưới gốc** là `timestamps`: chính các timestamp thật của đoạn (100 mốc, không đều). Cơ sở: Quy định 2.3 mục 4
  (nội suy/hình thang cho phép timestamp không đều). Không tạo lưới đều, không nội suy thêm mốc.
- **Làm thưa (Bước 5 của đề):** f2 giữ một mốc trong mỗi 2 mốc của lưới gốc (mốc 0, 2, 4…), f4 giữ một mốc
  trong mỗi 4 mốc (0, 4, 8…). Các điểm còn lại là **tập con của lưới gốc**, `y` giữ nguyên, không nội suy lại,
  luôn giữ cùng hai đầu; Q sẽ được chốt từ lưới gốc và giữ cố định khi làm thưa.
- Khi chỉ số mốc cuối của lưới gốc không chia hết cho 2 (hoặc 4), mốc cuối được **thêm vào** f2 (hoặc f4) để cùng
  hai đầu; khi đó bước cuối ngắn hơn bước thường. Ví dụ lưới có 100 mốc (chỉ số cuối 99) nên f2 có 51
  mốc, f4 có 26 mốc.
- Số mốc lưới không phải số quan sát thật độc lập; không coi lưới mới là quan sát độc lập.

## 6. Quy ước thống nhất

1. **Lưới gốc là timestamp thật** (`timestamps`); không dùng lưới đều.
2. **Q chốt một lần từ lưới gốc f1** (25%, 50%, 75% tổng hình thang của toàn đoạn), dùng chung cho f2, f4.
3. **Làm thưa = giữ tập con mốc của lưới gốc**, giá trị y giữ nguyên; thêm mốc cuối khi cần.
4. **Đoạn A và B xử lý riêng**; không ghép, không đi qua gap.
5. Đơn vị: thời gian là **phút**; `y` là **xe**; tích phân/chỉ số tích lũy là **xe·phút**. Số xe hiện diện không
   phải lưu lượng; I không phải tổng số xe duy nhất đi qua.
6. **Các điểm đang chờ giảng viên xác nhận** (nhóm tạm giả định như trên): "mỗi 2/4 mốc"
   là bước 2 và 4; cách thêm mốc cuối; các mức dung sai khảo sát; khi dừng chia đôi trả T = (a + b)/2 hay T = b (hiện dùng T = (a + b)/2).

## 7. Mô hình, thuật toán và kiểm chứng (Tuần 2)

### 7.1. Mô hình

Đánh số 0-based: ảnh k tại thời điểm t_k có y_k xe (k = 0…N, N+1 mốc); khoảng k nằm giữa ảnh k và ảnh k+1 (k = 0…N−1).

    h_k = t_(k+1) − t_k                      (phút)
    ỹ(t): nội suy tuyến tính từng đoạn qua các điểm (t_i, y_i)       (đề quy định)
    A_k = h_k · (y_k + y_(k+1)) / 2           (một hình thang, xe·phút)
    I_0 = 0,   I_(k+1) = I_k + A_k            (I_k = tải tích lũy tại t_k; I_tot = I_N)
    I(T) = I_k + y_k·s + m_k·s²/2             (T thuộc khoảng k, s = T − t_k, m_k = độ dốc khoảng k)
    F(T) = I(T) − Q,   Q = q · I_tot,   q ∈ {0,25; 0,5; 0,75}

- y là số xe hiện diện (`total_count`), nên I có đơn vị xe·phút, không phải tổng số xe đi qua.
- Có nghiệm khi F liên tục, F(t_0) = −Q < 0 và F(t_N) = (1 − q)·I_tot ≥ 0, tức 0 < q ≤ 1. Không ngoại suy ra ngoài [t_0, t_N].
- Khi có đoạn phẳng y = 0, T là thời điểm sớm nhất đạt Q.

### 7.2. Thuật toán chia đôi (tự cài đặt, float64)

    a, b = t_0, t_N                         (F(a) < 0 ≤ F(b), điều kiện hội tụ)
    lặp:  m = (a + b)/2
          nếu F(m) ≥ 0 thì b = m  (cập nhật cận trên; lấy nghiệm sớm nhất)
          ngược lại      a = m
    dừng khi b − a ≤ tol (10^-6 phút) hoặc đủ 100 vòng;  T = (a + b)/2

- Số vòng ≈ ⌈log2((t_N − t_0)/tol)⌉: đoạn A khoảng 27 vòng, đoạn B khoảng 26 vòng.
- Hai loại sai số tách riêng: sai số thời điểm (phút, theo độ rộng khoảng) và residual |F(T)| (xe·phút).
- Chia đôi hội tụ bậc 1 (mỗi vòng độ rộng giảm một nửa); công thức hình thang có sai số bậc 2 theo bước lưới h.
- Số điều kiện của T: |ΔT| ≈ |ΔI| / ỹ(T); nơi ỹ(T) nhỏ (ít xe) thì T nhạy hơn với sai số của I.

### 7.3. Kiểm chứng (`src/validate.py`)

| Bài kiểm chứng | Nội dung | Kết quả ghi vào |
|---|---|---|
| Hàm biết nghiệm đúng | y(t) = 1 + t trên [0, 1]: I(T) = T + T²/2, T* = −1 + √(1 + 2Q) với 0 < Q < 1,5. Báo sai số nghiệm (trị tuyệt đối của T − T*) và residual; MAE, RMSE, E_inf với tol = 10^-6 và 10^-12 | `verify_linear.csv`, `verify_linear_summary.csv` |

Trên y = 1 + t hình thang chính xác, nên sai số nghiệm chỉ do dung sai chia đôi và làm tròn float64.
Kết quả của lần chạy thử: sai số nghiệm luôn nhỏ hơn tol với mọi Q.

### 7.4. Khảo sát trên dữ liệu A/B (`src/experiments.py`)

Dữ liệu A/B không có nghiệm đúng, nên lưới gốc f1 (dung sai rất nhỏ) được dùng làm mốc so sánh.
- Làm thưa lưới (f2, f4, Q giữ nguyên từ f1): đo lệch |T(f) − T(f1)| bằng MAE, RMSE, E_inf; bậc hội tụ thực nghiệm p = log2(E_f4 / E_f2) (E_h ứng với f4, E_{h/2} ứng với f2); vì dữ liệu thật không trơn nên p chỉ mang tính chỉ báo.
- Dung sai: so T(tol) với T(10^-12) trên cùng lưới f1; độ lệch phải ≤ tol. Độ lệch do lấy mẫu thường lớn hơn nhiều độ lệch do dung sai.



## 8. Cách chạy

Python 3.10 trở lên. Cài thư viện (một lần):

    pip install numpy pandas

(Cài thêm `matplotlib` khi có `make_figures.py`.)

1. Chép `shared/analysis_snapshot.csv` vào thư mục `data/` của gói này.
2. Mở Terminal / cmd **tại thư mục chứa README này (thư mục gốc, không vào `src`)** và chạy:

       python src/run_all.py

Hoặc chạy riêng từng bước, theo thứ tự (bước 3 và 5 cần bước 0 chạy trước; bước 4 chạy độc lập):

| Bước | Lệnh | Việc làm |
|---|---|---|
| 00 | `python src/check_input.py` (thêm `--root <thư mục Traffic_BTL>` để kiểm tra cả ảnh) | Kiểm tra đầu vào |
| 0 | `python src/data_prep.py` | Tạo các đoạn A/B và lưới |
| 1–2 | `python src/integrate.py` | Tổng tải I_tot, Q (`integral_summary.csv`) |
| 3 | `python src/bisection.py` | Tìm T (`bisection_results.csv`) |
| 4 | `python src/validate.py` | Kiểm chứng và bảng sai số |
| 5 | `python src/experiments.py` | Làm thưa lưới, khảo sát dung sai |
| — | `python src/demo.py` | Chạy thử tương tác (nhập T, k hoặc q) |

Chương trình đọc đường dẫn tương đối từ vị trí của `config.json`, nên chuyển gói sang máy khác không cần sửa code.
Số rất nhỏ trong file CSV in dạng `e` (ví dụ `3.9e-07` nghĩa là 3,9 × 10^-7); `demo.py` hiển thị dạng 10^-7.
Kết quả: `data/segment_*.csv`, `data/grid_*_timestamps_f*.csv` và các file trong `results/` (mục 2).
Nếu có dòng mức `ERROR` trong bảng kiểm tra thì chương trình dừng. Mọi số liệu từ dữ liệu A/B đều là **sơ bộ** (PRELABEL).

## 9. Giới hạn và cập nhật sau nghiệm thu

- Nhãn hiện là PRELABEL: kết quả chỉ mang tính **sơ bộ**, có thể thay đổi sau khi cập nhật snapshot nghiệm thu.
- Đề tài dùng `total_count` trên toàn ảnh, không dùng số đo ROI. Giữ nguyên `roi_valid = False` và các số đo ROI
  trống khi chưa được xác nhận; không thay bằng 0.
- Tuần 5–6: chạy lại trên snapshot chính thức do giảng viên cung cấp sau nghiệm thu, rồi cập nhật bảng kết quả,
  hình vẽ và báo cáo.
- Không nộp thư mục môi trường ảo (`.venv`) khi đóng gói.
