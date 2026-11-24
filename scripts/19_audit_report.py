# -*- coding: utf-8 -*-
"""
Sinh audit_report.json - "phieu chan doan" cho tung cach chia du lieu.

Doc thang tu runs/ da chay, KHONG tinh lai chi so.
Nguong lay o docs/Project/Plans/Research/08_Tao_tac_SLI_va_giao_thuc_audit.md:
    SLI_user < 0,05         -> SAFE   (chia sach)
    0,05 <= SLI_user < 0,30 -> WARN   (con lot du lieu tuong lai)
    SLI_user >= 0,30        -> BLOCK  (khong dung duoc)
Rieng chuyen so sanh diem giua cac cach chia: neu so nguoi danh gia
chenh > 1,20 lan thi khong duoc so -> BLOCK.
"""
import json
import os

BASE = r"D:\Master Exers\Big Data\Recomendation_System"

COMPARE = os.path.join(
    BASE, "runs", "20261120_012944_09_compare_and_reversal_21d0811a",
    "outputs", "comparison.json")
AUDIT = os.path.join(
    BASE, "runs", "20261115_233616_05_audit_split_leakage_3fa5a49e",
    "outputs", "data_level_audit.json")
OUT = os.path.join(
    BASE, "docs", "Project", "Main", "Presentation", "Slides",
    "audit_report.json")

SPLIT_VI = {
    "random80_20": "trộn ngẫu nhiên 80/20",
    "temporal_global": "cắt theo mốc thời gian toàn cục",
    "leave_one_out": "giữ lượt chấm cuối của mỗi người",
}


def f2(x):
    """So thap phan kieu Viet Nam: 98,92"""
    return ("%.2f" % x).replace(".", ",")


def f1(x):
    return ("%.1f" % x).replace(".", ",")


def i1000(n):
    """162541 -> 162.541"""
    return "{:,}".format(n).replace(",", ".")


def verdict_sli(sli_user):
    if sli_user >= 0.30:
        return "BLOCK"
    if sli_user >= 0.05:
        return "WARN"
    return "SAFE"


def main():
    for path in (COMPARE, AUDIT):
        if not os.path.exists(path):
            raise SystemExit("Thiếu file nguồn: " + path)

    compare = json.load(open(COMPARE, encoding="utf-8"))
    audit = json.load(open(AUDIT, encoding="utf-8"))["audits"]

    rows = {r["split"]: r for r in compare["rows"]}
    order = ["random80_20", "temporal_global", "leave_one_out"]

    users = {s: rows[s]["eval_users_als"] for s in order}
    biggest = max(users.values())
    global_ratio = biggest / min(users.values())

    records = []
    for split in order:
        r = rows[split]
        a = audit[split]
        sli_user = a["temporal_violation_user_pct"] / 100.0
        sli_global = a["temporal_violation_global_pct"] / 100.0
        unseen = r["unseen_item_pct"]
        users_n = users[split]
        own_ratio = biggest / users_n

        v_sli = verdict_sli(sli_user)
        comparable = own_ratio <= 1.20
        verdict = v_sli if comparable else "BLOCK"

        parts = []
        if v_sli == "BLOCK":
            parts.append(
                "Rò rỉ %s%% số dòng test: những dòng này cũ hơn lượt chấm "
                "mới nhất của chính người đó, tức mô hình đã nhìn thấy tương "
                "lai của người ấy. Không dùng điểm số này để kết luận."
                % f2(sli_user * 100))
        elif v_sli == "WARN":
            parts.append(
                "Rò rỉ %s%% số dòng test, nằm trong khoảng 0,05–0,30: dùng "
                "được nhưng phải ghi chú là còn lẫn dữ liệu tương lai."
                % f2(sli_user * 100))
        else:
            parts.append(
                "Rò rỉ %s%% số dòng test: không có dòng nào cũ hơn lượt "
                "chấm mới nhất của người đó." % f2(sli_user * 100))

        if not comparable:
            if users_n == biggest:
                parts.append(
                    "Đây là cách chia có nhiều người được chấm điểm nhất "
                    "(%s người), nên nó là mốc để so." % i1000(users_n))
            else:
                parts.append(
                    "Nhưng chỉ chấm được %s người, bằng %s%% của cách chia "
                    "lớn nhất (%s người) — lệch %s lần, vượt ngưỡng 1,20. "
                    "Vì vậy không được nói 'mô hình này tốt hơn', chỉ được "
                    "nói 'điểm cao hơn trên một mẫu khác'."
                    % (i1000(users_n), f1(100.0 * users_n / biggest),
                       i1000(biggest), f1(own_ratio)))

        if unseen >= 5.0:
            parts.append(
                "%s%% số dòng test trỏ tới phim chưa từng xuất hiện trong "
                "train (phim mới hoàn toàn) — phần điểm này không phản ánh "
                "khả năng gợi ý cho người dùng cũ." % f2(unseen))

        records.append({
            "split": split,
            "split_vi": SPLIT_VI[split],
            "sli_user_pct": round(sli_user * 100, 4),
            "sli_global_pct": round(sli_global * 100, 4),
            "eval_users": users_n,
            "unseen_item_pct": round(unseen, 4),
            "verdict": verdict,
            "verdict_sli": v_sli,
            "comparable_with_other_splits": comparable,
            "reason": " ".join(parts),
        })

    report = {
        "report": "Phiếu chẩn đoán cách chia dữ liệu",
        "explain": (
            "Mỗi cách chia dữ liệu nhận một phiếu. Đọc từ trên xuống: mức rò "
            "rỉ, số người thật sự được chấm điểm, rồi mới tới kết luận. "
            "SAFE = dùng được; WARN = dùng được nhưng phải ghi chú; "
            "BLOCK = không được dùng để so sánh."),
        "thresholds": {
            "sli_user_pct": {"safe": "nhỏ hơn 0,05",
                             "warn": "0,05 đến 0,30",
                             "block": "từ 0,30 trở lên"},
            "note": "Ba ngưỡng do đề tài tự đặt, không phải chuẩn công bố.",
            "eval_users_ratio_block": "lệch hơn 1,20 lần thì cấm so sánh",
        },
        "eval_users_ratio_max_over_min": round(global_ratio, 4),
        "sources": {
            "comparison": COMPARE,
            "audit": AUDIT,
            "protocol_id": compare.get("protocol_id"),
            "seed": compare.get("seed"),
            "k": compare.get("k"),
        },
        "splits": records,
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)

    print("OK", OUT, os.path.getsize(OUT), "bytes")
    for rec in records:
        print(" %-16s SLI_user=%6.2f%%  users=%7d  unseen=%6.2f%%  %-5s -> %s"
              % (rec["split"], rec["sli_user_pct"], rec["eval_users"],
                 rec["unseen_item_pct"], rec["verdict_sli"], rec["verdict"]))
    print(" ti le nguoi lon nhat / nho nhat =", round(global_ratio, 3))


if __name__ == "__main__":
    main()
