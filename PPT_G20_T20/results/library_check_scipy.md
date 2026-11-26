# So thêm với scipy (Level 2 bổ sung) - Đề 20

Lưới gốc f1. scipy.optimize.bisect dùng CÙNG thuật toán chia đôi, cùng tol = 1e-06 phút;
scipy.optimize.brentq (xtol = 1e-14) coi như nghiệm chuẩn. File này chỉ tạo khi máy có scipy.

| Đoạn | Mức | T tự viết (phút) | T scipy.bisect | T scipy.brentq | Lệch với bisect | Lệch với brentq |
|---|---|---|---|---|---|---|
| A | 25% | 17.806182102 | 17.806182357 | 17.806181889 | 2.551e-07 | 2.129e-07 |
| A | 50% | 37.443147033 | 37.443146523 | 37.443146988 | 5.101e-07 | 4.525e-08 |
| A | 75% | 53.288040417 | 53.288039907 | 53.288040175 | 5.101e-07 | 2.424e-07 |
| B | 25% | 11.630729184 | 11.630728822 | 11.630729167 | 3.617e-07 | 1.726e-08 |
| B | 50% | 25.026042003 | 25.026041641 | 25.026041667 | 3.617e-07 | 3.361e-07 |
| B | 75% | 35.936018284 | 35.936018284 | 35.936018083 | 1.421e-14 | 2.015e-07 |

- Lệch lớn nhất với scipy.bisect: 5.101e-07 phút (ngưỡng tol = 1e-06: ĐẠT)
- Lệch lớn nhất với scipy.brentq: 3.361e-07 phút (ngưỡng tol/2 = 5e-07: ĐẠT)

Ghi chú: hai cách chia đôi cùng nằm trong ±tol/2 quanh nghiệm thật nhưng lấy điểm trả về khác nhau
(code nhóm lấy T = b sau khi b − a ≤ tol/2), nên lệch nhau tối đa tol.
