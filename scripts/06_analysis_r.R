## ============================================================================
## Phan tich ket qua audit bang R + SparkR
## Project: D:\Master Exers\Big Data\Recomendation_System
## Chay:  "C:\Program Files\R\R-4.6.2\bin\Rscript.exe" scripts\06_analysis_r.R
## Yeu cau: .libPaths include 'D:/R-library'
## ============================================================================

.libPaths(c("D:/R-library", .libPaths()))
suppressPackageStartupMessages({
  library(jsonlite); library(dplyr); library(ggplot2); library(mongolite); library(corrplot)
})

POC_DIR  <- "D:/recsys_data/poc"
OUT_DIR  <- "D:/recsys_data/reports"
FIG_DIR  <- paste0(OUT_DIR, "/figures")
MONGO    <- "mongodb://localhost:27017"
dir.create(OUT_DIR, recursive = TRUE, showWarnings = FALSE)
dir.create(FIG_DIR, recursive = TRUE, showWarnings = FALSE)

SPLITS <- c("random80_20", "temporal_global", "leave_one_out")

## ---- 1. Doc JSON ket qua (1 file cho moi split) ----
rows <- list()
for (s in SPLITS) {
  f <- file.path(POC_DIR, paste0("poc6_", s, ".json"))
  if (!file.exists(f)) { cat("MISSING:", f, "\n"); next }
  R <- fromJSON(f, simplifyVector = FALSE)
  base <- data.frame(
    split         = s,
    train_rows    = R$train_rows,
    test_rows     = R$test_rows,
    viol_global   = R$temporal_violation_global_pct,
    viol_user     = R$temporal_violation_user_pct,
    unseen_item   = R$unseen_item_pct,
    cold_user     = R$coldstart_user_rows,
    eval_users    = R$eval_users,
    eval_test     = R$eval_test_rows,
    eval_rel_users= R$eval_relevant_users,
    rel_rows      = R$test_relevant_eval_rows,
    stringsAsFactors = FALSE)
  for (mk in c("popularity", "als")) {
    m <- R[[mk]]
    if (is.null(m) || !is.null(m$error)) next
    rows[[length(rows) + 1]] <- data.frame(
      split = s, model = m$model,
      ndcg10 = m$ndcg10, hit10 = if (is.null(m$hit_rate10)) NA else m$hit_rate10,
      cov = m$catalog_coverage, tail = m$longtail_coverage,
      gini = m$gini_exposure,
      bias = m$popularity_bias_ratio,
      avg_pop_rec = m$avg_pop_rec, avg_pop_all = m$avg_pop_all,
      n_eval = m$eval_users, stringsAsFactors = FALSE)
  }
}
metrics <- bind_rows(rows)
base_tab <- bind_rows(lapply(SPLITS, function(s) {
  f <- file.path(POC_DIR, paste0("poc6_", s, ".json"))
  if (!file.exists(f)) return(NULL)
  R <- fromJSON(f, simplifyVector = FALSE)
  data.frame(split = s, train_rows = R$train_rows, test_rows = R$test_rows,
             viol_global = R$temporal_violation_global_pct,
             viol_user = R$temporal_violation_user_pct,
             unseen_item = R$unseen_item_pct, cold_user = R$coldstart_user_rows,
             eval_users = R$eval_users, eval_rel_users = R$eval_relevant_users,
             stringsAsFactors = FALSE)
}))

cat("\n=== 1. METRICS CAU DU LIEU ===\n"); print(as.data.frame(base_tab))
cat("\n=== 2. METRICS HIEU QUA + BIAS ===\n"); print(as.data.frame(metrics))

## ---- 3. Doc MongoDB (chi doc) + ghi bang chung rieng ----
## R KHONG duoc drop/insert vao recsys.audit_metrics: schema day du (nhieu field)
## duoc scripts/05_store_mongodb.py ghi. R chi doc de kiem tra + sinh bieu do.
## Bang chung rieng: recsys.audit_metrics_r (schema rut gon, phuc vu bao cao).
mongo_ro <- mongo(url = MONGO, db = "recsys", collection = "audit_metrics")
cat("\nMongoDB recsys.audit_metrics:", mongo_ro$count(), "docs (nguon ghi: 05_store_mongodb.py)\n")

mongo_write <- mongo(url = MONGO, db = "recsys", collection = "audit_metrics_r")
mongo_write$drop()
mongo_write$insert(vapply(seq_len(nrow(metrics)), function(i) {
  d <- as.list(metrics[i, ]); names(d) <- names(metrics)
  as.character(toJSON(d, auto_unbox = TRUE, na = "null", digits = 8))
}, character(1)))
cat("MongoDB recsys.audit_metrics_r:", mongo_write$count(), "docs (bang chung rut gon)\n")

## ---- 4. Kiem dinh: co dao chieu thu tu khong? ----
## So sanh NDCG cua 2 model giua 3 split. Tinh Spearman rho cho tung cap split.
cat("\n=== 3. THU TU MODEL (Spearman) ===\n")
sp <- lapply(SPLITS, function(s) {
  sub <- metrics %>% filter(split == s) %>% arrange(desc(ndcg10))
  if (nrow(sub) < 2) return(NULL)
  data.frame(split = s,
             order = paste(sub$model, collapse = " > "),
             ndcg_pop = sub$ndcg10[1], ndcg_als = sub$ndcg10[2])
}) %>% bind_rows()
print(as.data.frame(sp))

## ---- 5. Do lon tuong doi cua thu tu (normalized) ----
metrics$ndcg_norm <- metrics$ndcg10 / max(metrics$ndcg10[metrics$model == "ALS_implicit"], na.rm = TRUE)
cat("\n=== 4. NDCG CHUAN HOA THEO SPLIT ===\n")
print(as.data.frame(metrics %>% select(split, model, ndcg10, ndcg_norm, bias, gini)))

## ---- 6. Bieu do ----
p1 <- ggplot(metrics, aes(x = split, y = ndcg10, fill = model)) +
  geom_col(position = position_dodge(width = 0.7), width = 0.65) +
  geom_text(aes(label = round(ndcg10, 4)), position = position_dodge(width = 0.7), vjust = -0.4, size = 3) +
  labs(title = "NDCG@10 theo chiến lược chia tập dữ liệu",
       x = NULL, y = "NDCG@10", fill = "Mô hình") +
  theme_minimal(base_size = 11) + theme(legend.position = "bottom")
ggsave(file.path(FIG_DIR, "fig1_ndcg_by_split.png"), p1, width = 8, height = 4.5, dpi = 150)

p2 <- ggplot(metrics, aes(x = split, y = bias, fill = model)) +
  geom_col(position = position_dodge(width = 0.7), width = 0.65) +
  geom_hline(yintercept = 1, linetype = "dashed", color = "red") +
  labs(title = "Popularity bias ratio (>1 = thiên lệch về phim phổ biến)",
       x = NULL, y = "avg_pop_rec / avg_pop_all", fill = "Mô hình") +
  scale_y_log10() + theme_minimal(base_size = 11) + theme(legend.position = "bottom")
ggsave(file.path(FIG_DIR, "fig2_popularity_bias.png"), p2, width = 8, height = 4.5, dpi = 150)

p3 <- ggplot(metrics, aes(x = split, y = gini, fill = model)) +
  geom_col(position = position_dodge(width = 0.7), width = 0.65) +
  labs(title = "Gini mức phơi bày (cao = tập trung vào ít phim phổ biến)",
       x = NULL, y = "Gini exposure", fill = "Mô hình") +
  theme_minimal(base_size = 11) + theme(legend.position = "bottom")
ggsave(file.path(FIG_DIR, "fig3_gini_exposure.png"), p3, width = 8, height = 4.5, dpi = 150)

p4 <- ggplot(base_tab, aes(x = split)) +
  geom_col(aes(y = viol_global, fill = "Vi phạm toàn cục"), position = "dodge") +
  geom_col(aes(y = viol_user, fill = "Vi phạm tương đối user"), position = "dodge") +
  labs(title = "Tỷ lệ rò rỉ thời gian theo định nghĩa",
       x = NULL, y = "% tương tác test vi phạm", fill = NULL) +
  theme_minimal(base_size = 11) + theme(legend.position = "bottom")
ggsave(file.path(FIG_DIR, "fig4_temporal_leakage.png"), p4, width = 8, height = 4.5, dpi = 150)

p5 <- ggplot(metrics, aes(x = split, y = cov, fill = model)) +
  geom_col(position = position_dodge(width = 0.7), width = 0.65) +
  labs(title = "Độ phủ danh mục (catalog coverage)",
       x = NULL, y = "Tỷ lệ item được đề xuất", fill = "Mô hình") +
  theme_minimal(base_size = 11) + theme(legend.position = "bottom")
ggsave(file.path(FIG_DIR, "fig5_catalog_coverage.png"), p5, width = 8, height = 4.5, dpi = 150)

p6 <- ggplot(metrics, aes(x = split, y = tail, fill = model)) +
  geom_col(position = position_dodge(width = 0.7), width = 0.65) +
  labs(title = "Độ phủ đuôi dài (long-tail coverage)",
       x = NULL, y = "Tỷ lệ item đuôi dài được đề xuất", fill = "Mô hình") +
  theme_minimal(base_size = 11) + theme(legend.position = "bottom")
ggsave(file.path(FIG_DIR, "fig6_longtail_coverage.png"), p6, width = 8, height = 4.5, dpi = 150)

## ---- 7. Ma tran tuong quan cac chi so ----
## bo 'tail' (longtail_coverage = 0 o ca 6 dong -> SD = 0, khong tinh duoc)
cm <- metrics %>% select(ndcg10, cov, gini, bias) %>% cor(use = "complete.obs")
cat("\n=== 5. MA TRAN TUONG QUAN ===\n"); print(round(cm, 3))
png(file.path(FIG_DIR, "fig7_corrplot.png"), width = 1400, height = 1200, res = 150)
corrplot(cm, method = "circle", type = "lower", tl.col = "black", addCoef.col = "black",
         number.digits = 2)
dev.off()

## ---- 8. Luu bang tong hop ----
write.csv(metrics, file.path(OUT_DIR, "metrics_summary.csv"), row.names = FALSE)
write.csv(base_tab, file.path(OUT_DIR, "data_level_metrics.csv"), row.names = FALSE)
cat("\nDa luu:", OUT_DIR, "\n")
cat("Figures:", FIG_DIR, "\n")
cat("=== DONE ===\n")
