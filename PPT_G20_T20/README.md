# Nhóm 20 — Đề tài 20 — Thời điểm đạt chỉ số tải tích lũy

Đề tài: cho hàm tải y(t) (số xe hiện diện theo thời gian), tìm thời điểm T sao cho tích phân tích lũy
I(T) = ∫ y(t) dt từ đầu đoạn đến T đạt ngưỡng Q (25%, 50%, 75% tổng tải của đoạn).

## 1. Phạm vi và trạng thái

Gói này minh chứng việc **chọn, kiểm tra hai đoạn A/B và chuẩn bị dữ liệu** trong Tuần 1 (khung code chạy bằng
đường dẫn tương đối). Phần tính toán chính (tích phân hình thang, chia đôi, kiểm chứng, bảng sai số) **chưa nằm
trong gói này**; xem mục 7. Đây không phải hồ sơ hoàn chỉnh của phần Phương pháp tính 6 điểm.

Dữ liệu camera hiện mang nhãn `unreviewed_prelabel` (PRELABEL, chưa nghiệm thu). Mọi con số tính từ dữ liệu
này là **SƠ BỘ**, không phải ground truth. Không tự đổi trạng thái nhãn thành `human_verified`.

## 2. Thành phần gói

| Đường dẫn | Nội dung |
|---|---|
| `config.json` | Tham số của dự án: seed 2026, kiểu `float64`, bước h0 = 30 giây, các kiểu lưới gốc, hệ số làm thưa lưới, các mức Q, dung sai chia đôi, đơn vị |
| `data/analysis_snapshot.csv` | Bản chép của `shared/analysis_snapshot.csv` (giảng viên cung cấp). Tự chép vào trước khi chạy |
| `data/segment_A.csv`, `data/segment_B.csv` | Hai đoạn quan sát nguồn (giữ nguyên số đếm và nhãn); cột `t_min` là thời gian tính bằng phút từ mốc đầu đoạn |
| `data/grid_A_timestamps_f1.csv`, `grid_B_timestamps_f1.csv` | **Lưới gốc chính:** timestamp thật (100 mốc, không đều). Cơ sở: Quy định 2.3 mục 4 (nội suy/hình thang cho phép timestamp không đều) |
| `data/grid_*_timestamps_f2.csv`, `..._f4.csv` | **Làm thưa mỗi 2 / mỗi 4 mốc** của lưới gốc chính (giữ mốc 0, 2, 4… / 0, 4, 8…), `y` giữ nguyên, luôn giữ mốc cuối nên cùng hai đầu |
| `data/grid_A_regular30s_f1.csv`, `grid_B_regular30s_f1.csv` | *Phương án dự phòng:* lưới đều 30 giây (h0 = 0,5 phút), nội suy tuyến tính từng đoạn; bắt đầu ở mốc đầu, kết thúc ở mốc h0 cuối còn nằm trong đoạn (A: 137 mốc, 0–68,0 phút; B: 98 mốc, 0–48,5 phút) |
| `data/grid_*_regular30s_f2.csv`, `..._f4.csv` | Làm thưa mỗi 2 / mỗi 4 mốc của lưới đều dự phòng, giá trị `y` giữ nguyên; luôn giữ mốc cuối của lưới gốc |
| `src/common.py` | Hàm dùng chung: đọc cấu hình, đặt seed, đường dẫn tương đối, kiểu `float64` |
| `src/data_prep.py` | Đọc snapshot, kiểm tra hai đoạn A/B, đổi thời gian ra phút, tạo các lưới |
| `src/run_all.py` | Script chạy lại tự động; hiện mới gọi bước chuẩn bị dữ liệu, các bước sau tự được bỏ qua nếu chưa có file |
| `results/data_validation.csv` | Bảng kiểm tra dữ liệu A/B (giải thích ở mục 4) |
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
| `luoi_regular30s_f1_so_moc` | Số mốc lưới đều 30 giây (A: 137, B: 98); f2 và f4 là bản làm thưa mỗi 2 và mỗi 4 mốc |
| `luoi_regular30s_f1_dau_cuoi_phut` | Mốc đầu và mốc cuối của lưới đều (A: 0–68,0; B: 0–48,5), dừng ở mốc 30 giây cuối còn trong đoạn |
| `luoi_regular30s_du_80_moc` | Kiểm tra lưới đều có đủ 80 mốc không (quy định: nếu thiếu thì chọn đoạn dài hơn); cả hai đạt |
| `luoi_timestamps_f1_so_moc` | Số mốc lưới timestamp thật: 100 ở cả hai đoạn |
| `luoi_timestamps_f2/f4_...` | 51 mốc và 26 mốc, vẫn giữ mốc đầu và mốc cuối thật (A: 0–68,4667; B: 0–48,55) |

**Kết luận:** cột `level` của hai đoạn chỉ có OK, INFO và một dòng WARN về nhãn, không có ERROR, nên dữ liệu
đủ điều kiện để chạy bước tiếp theo.

### 4.3. "Hợp lệ" ở đây có nghĩa gì

- **Có nghĩa:** hai đoạn thoả các điều kiện trong Quy định mục 2.3 mà nhóm kiểm tra bằng code (`data_prep.py`).
- **Không có nghĩa:** dữ liệu đã được giảng viên nghiệm thu. Bảng này do nhóm tự kiểm tra, không phải công cụ QC
  của giảng viên (`qc_dataset.py` dùng cho nhãn ảnh ở Phần 1).
- **Giới hạn hiện tại:** khi gặp khoảng trống lớn hơn 3 lần trung vị, quy định yêu cầu *tách đoạn*; code hiện *dừng và
  báo ERROR* để nhóm xử lý. Với dữ liệu hiện tại không có gap nên không xảy ra. Nhóm cũng chưa tự động đối chiếu
  tên recording với ngày của timestamp và chưa ghi file danh sách bản ghi bị loại (hiện không có bản ghi trùng).

## 5. Lưới gốc và làm thưa lưới

- `segment_A.csv`, `segment_B.csv` là đầu vào chính: timestamp thật (ISO 8601), giữ nguyên giây.
- **Lưới gốc** có hai biến thể (cả hai đều được tạo; chọn biến thể nào sẽ chốt sau khi giảng viên xác nhận):
  - `timestamps` (**lưới chính**): chính các timestamp thật của đoạn (Quy định 2.3 mục 4: nội suy/hình thang cho
    phép timestamp không đều).
  - `regular30s` (*phương án dự phòng*, vì Quy định chỉ bắt buộc lưới đều 30 giây cho sai phân, Simpson, ODE):
    lưới đều h0 = 30 giây = 0,5 phút (không phải 0,5 giây), nội suy tuyến tính trong từng đoạn, không ngoại suy,
    kết thúc ở mốc h0 cuối còn trong đoạn. Giá trị `y` thập phân là kết quả nội suy, không phải số xe quan sát nguyên.
- **Làm thưa (Bước 5 của đề):** f2 giữ một mốc trong mỗi 2 mốc của lưới gốc (mốc 0, 2, 4…), f4 giữ một mốc
  trong mỗi 4 mốc (0, 4, 8…). Các điểm còn lại là **tập con của lưới gốc**, `y` giữ nguyên, không nội suy lại,
  luôn giữ cùng hai đầu; Q sẽ được chốt từ lưới gốc và giữ cố định khi làm thưa.
- Khi chỉ số mốc cuối của lưới gốc không chia hết cho 2 (hoặc 4), mốc cuối được **thêm vào** f2 (hoặc f4) để cùng
  hai đầu; khi đó bước cuối ngắn hơn bước thường. Ví dụ lưới `timestamps` có 100 mốc (chỉ số cuối 99) nên f2 có 51
  mốc, f4 có 26 mốc; lưới `regular30s` đoạn A (chỉ số cuối 136) chia hết nên không cần thêm, đoạn B (97) thì phải thêm.
- Số mốc lưới không phải số quan sát thật độc lập; không coi lưới mới là quan sát độc lập.

## 6. Quy ước thống nhất

1. **Mỗi lần chạy chỉ dùng MỘT kiểu lưới gốc** (`timestamps` hoặc `regular30s`) từ đầu đến cuối; không trộn hai bộ.
2. **Hai kiểu lưới có tổng tích phân khác nhau**: `regular30s` dừng sớm hơn mốc cuối thật (A: 68,0 so với 68,4667;
   B: 48,5 so với 48,55) vì không được ngoại suy, nên Q của hai kiểu không so sánh trực tiếp được.
3. **Q chốt một lần từ lưới gốc f1** (25%, 50%, 75% tổng hình thang của toàn đoạn), dùng chung cho f2, f4.
4. **Làm thưa = giữ tập con mốc của lưới gốc**, giá trị y giữ nguyên; thêm mốc cuối khi cần.
5. **Đoạn A và B xử lý riêng**; không ghép, không đi qua gap.
6. Đơn vị: thời gian là **phút**; `y` là **xe**; tích phân/chỉ số tích lũy là **xe·phút**. Số xe hiện diện không
   phải lưu lượng; I không phải tổng số xe duy nhất đi qua.
7. **Các điểm đang chờ giảng viên xác nhận** (nhóm tạm giả định như trên): lưới gốc là timestamp thật; "mỗi 2/4 mốc"
   là bước 2 và 4; cách thêm mốc cuối; hàm bổ sung để đo bậc hội tụ; các mức dung sai khảo sát.

## 7. Kế hoạch phần tính toán


    h_i = t_(i+1) − t_i
    ỹ(t): nội suy tuyến tính từng đoạn qua các điểm (t_i, y_i)
    I(T) = S_k + y_k·s + m_k·s²/2        (s = T − t_k, m_k = độ dốc đoạn k, S_k = tích lũy đến t_k)
    F(T) = I(T) − Q ;  tìm T nhỏ nhất sao cho F(T) = 0 bằng chia đôi

- Dung sai chia đôi 1e-6 phút, tối đa 100 vòng; cập nhật cận trên khi F(m) ≥ 0 để lấy nghiệm sớm nhất.
- Kiểm chứng trên hàm biết nghiệm: y(t) = 1 + t, I(T) = T + T²/2, T = −1 + √(1 + 2Q) với 0 < Q < 1,5.
- Lõi (nội suy, hình thang, chia đôi) **tự cài đặt** bằng `float64`; thư viện chỉ dùng để đối chứng và vẽ hình.
- Sẽ bổ sung: `src/integrate.py`, `src/bisection.py`, `src/validate.py`, `src/experiments.py`, `src/make_figures.py`,
  thư mục `results/` (bảng sai số MAE, RMSE, E_inf, bậc hội tụ p), `slides.pdf`, `report.pdf`, `contributions.csv`.

## 8. Cách chạy

Python 3.10 trở lên. Cài thư viện (một lần):

    pip install numpy pandas

1. Chép `shared/analysis_snapshot.csv` vào thư mục `data/` của gói này.
2. Mở Terminal / cmd tại thư mục chứa README này và chạy:

       python src/run_all.py

Chương trình đọc đường dẫn tương đối từ vị trí của `config.json`, nên chuyển gói sang máy khác không cần sửa code.
Kết quả: `data/segment_A.csv`, `data/segment_B.csv`, `data/grid_*_<regular30s|timestamps>_f*.csv`,
`results/data_validation.csv`. Nếu có dòng mức `ERROR` trong bảng kiểm tra thì chương trình dừng.

## 9. Giới hạn và cập nhật sau nghiệm thu

- Nhãn hiện là PRELABEL: kết quả chỉ mang tính **sơ bộ**, có thể thay đổi sau khi cập nhật snapshot nghiệm thu.
- Đề tài dùng `total_count` trên toàn ảnh, không dùng số đo ROI. Giữ nguyên `roi_valid = False` và các số đo ROI
  trống khi chưa được xác nhận; không thay bằng 0.
- Tuần 5–6: chạy lại trên snapshot chính thức do giảng viên cung cấp sau nghiệm thu, rồi cập nhật bảng kết quả,
  hình vẽ và báo cáo.
- Không nộp thư mục môi trường ảo (`.venv`) khi đóng gói.
